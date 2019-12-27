import socket
import datetime
import json
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.model.models import User, UserLogin, Message, Group, GroupUsers


class Server:
    """
    服务器类
    """

    def __init__(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__engine = create_engine('sqlite:///server/data/ChatServer.db')
        self.__DBSession = sessionmaker(bind=self.__engine)
        # self.__sqlite_conn = sqlite3.connect('./server_sql/ChatServer.db')
        # self.__cursor = self.__sqlite_conn.cursor()
        self.__connections = [None] * 1000

    def __user_thread(self, uid):
        """
        用户子线程，用于处理用户的socket请求
        :param uid: 用户id
        :return: 0
        """
        connection = self.__connections[uid]

        while True:
            try:
                buffer = connection.recv(1024).decode()
                obj = json.loads(buffer)
                print(obj)
                if obj['type'] == 'message':
                    session = self.__DBSession()
                    user_message = Message(sender_uid=obj['sender_uid'], sender_ip=obj['sender_ip'],
                                           receiver_uid=obj['receiver_uid'], message=obj['message'],
                                           group_gid=obj['group_gid'],
                                           create_time=datetime.datetime.strptime(obj['create_time'],
                                                                                  "%Y-%m-%d %H:%M:%S.%f"))
                    session.add(user_message)
                    session.commit()
                    mid = user_message.mid
                    session.close()
                    # print(mid)

                    thread = threading.Thread(target=self.__send_message_thread, args=(mid,))
                    thread.setDaemon(True)
                    thread.start()
                elif obj['type'] == 'group':
                    if obj['action'] == 'create':
                        session = self.__DBSession()
                        new_group = Group(group_name=obj['group_name'],
                                          create_time=datetime.datetime.strptime(obj['create_time'],
                                                                                 "%Y-%m-%d %H:%M:%S.%f"))
                        session.add(new_group)
                        session.commit()
                        new_gid = new_group.gid
                        new_group_user = GroupUsers(gid=new_gid, uid=obj['creater_uid'],
                                                    join_time=datetime.datetime.strptime(obj['create_time'],
                                                                                         "%Y-%m-%d %H:%M:%S.%f"))
                        session.add(new_group_user)
                        session.commit()
                        session.close()
                        connection.send(json.dumps({
                            'type': 'info',
                            'field': 'group',
                            'action': 'create',
                            'gid': new_gid,
                            'status': 'success'
                        }).encode())
                    elif obj['action'] == 'join':
                        self.__user_join_group(obj['uid'], obj['group_gid'])
                        session = self.__DBSession()
                        connection.send(json.dumps({
                            'type': 'info',
                            'field': 'group',
                            'group_name': session.query(Group.group_name).filter(Group.gid == obj['group_gid']).first()[0],
                            'action': 'join',
                            'status': 'success'
                        }).encode())
                else:
                    print('无法解析')

            except Exception as e:
                print(e)
                print('\033[1;33;33m[Server]\033[0m 用户已离线:', connection.getsockname(), connection.fileno())
                self.__user_logout(uid)
                self.__connections[uid].close()
                self.__connections[uid] = None
                return 0

    def __send_message_thread(self, mid):
        """
        发送信息子线程
        :param mid: 信息id
        :return: True/False
        """
        session = self.__DBSession()
        message = session.query(Message).filter(Message.mid == mid).first()
        # 消息是否存在
        if message:
            # 消息是否为单一接收者
            if message.receiver_uid:
                # 接收方是否在线
                if self.__connections[message.receiver_uid]:
                    print(message.receiver_uid)
                    self.__connections[message.receiver_uid].send(json.dumps({
                        'type': 'message',
                        'sender_uid': message.sender_uid,
                        'sender_ip': message.sender_ip,
                        'sender_nickname': session.query(User.nickname).filter(User.uid == message.sender_uid).first()[0],
                        'receiver_uid': message.receiver_uid,
                        'message': message.message,
                        'group_gid': '',
                        'group_name': '',
                        'create_time': str(message.create_time)
                    }).encode())
                return True
            # 接收方为群组
            elif message.group_gid:
                group_users = session.query(GroupUsers.uid).filter(GroupUsers.gid == message.group_gid)
                for receiver, in group_users:
                    if self.__connections[int(receiver)]:
                        self.__connections[int(receiver)].send(json.dumps({
                            'type': 'message',
                            'sender_uid': message.sender_uid,
                            'sender_ip': message.sender_ip,
                            'sender_nickname': session.query(User.nickname).filter(User.uid == message.sender_uid).first()[0],
                            'receiver_uid': '',
                            'message': message.message,
                            'group_gid': message.group_gid,
                            'group_name': session.query(Group.group_name).filter(Group.gid == message.group_gid).first()[0],
                            'create_time': str(message.create_time)
                        }).encode())
                return True
        else:
            return False

    # def list_all_user(self):
    #     """
    #     在print输出中显示所有用户
    #     :return:none
    #     """
    #     result = self.__cursor.execute('''SELECT * FROM users''')
    #     for row in result:
    #         print(row)

    def __create_user(self, nickname, password):
        """
        在数据库中新建一个用户
        :param nickname: 用户名
        :param password: 密码
        :return: new_user_uid:新注册用户的uid
        """
        session = self.__DBSession()
        new_user = User(nickname=nickname, password=password)
        session.add(new_user)
        session.commit()
        new_user_uid = new_user.uid
        session.close()
        return new_user_uid

    def __user_join_group(self, uid, gid):
        """
        用户加入组
        :param uid: 用户id
        :param gid: 组id
        :return: none
        """
        session = self.__DBSession()
        relation = session.query(GroupUsers).filter(GroupUsers.uid == uid, GroupUsers.gid == gid).first()
        if relation:
            session.close()
            return True
        new_group_user = GroupUsers(uid=uid, gid=gid, join_time=datetime.datetime.now())
        session.add(new_group_user)
        session.commit()
        session.close()
        return True

    def __create_group(self, group_name, uid):
        """
        在数据库中新建一个组, 并添加第一位组成员
        :param group_name: 组名
        :param uid: 首位成员id
        :return: new_group_gid: 新建组的组号
        """
        session = self.__DBSession()
        new_group = Group(group_name=group_name, create_time=datetime.datetime.now())
        session.add(new_group)
        session.commit()
        new_group_gid = new_group.gid
        session.close()
        self.__user_join_group(uid, new_group_gid)
        return new_group_gid

    def __user_login(self, uid, password, ip_address):
        """
        用户登陆函数
        :param uid: 用户id
        :param password: 用户密码
        :param ip_address: 用户ip
        :return: True/False
        """
        session = self.__DBSession()
        login_user = session.query(User).filter(User.uid == uid, User.password == password).first()
        # 是否存在该用户
        if login_user:
            logined_user = session.query(UserLogin).filter(UserLogin.uid == uid).first()
            # print(logined_user)
            # 该用户是否已登录
            if logined_user:
                logined_user.ip_address = ip_address
                logined_user.login_time = datetime.datetime.now()
                session.commit()
                user_nickname = login_user.nickname
                print('登陆成功!')
                session.close()
                return user_nickname
            else:
                new_login_user = UserLogin(uid=uid, ip_address=ip_address, login_time=datetime.datetime.now())
                session.add(new_login_user)
                session.commit()
                user_nickname = login_user.nickname
                print('用户已经登陆!')
                session.close()
                return str(user_nickname)
        else:
            print('用户名或密码错误!')
            return False

    def __user_logout(self, uid):
        """
        用户离线/登出
        :param uid: 用户id
        :return: True/False
        """
        session = self.__DBSession()
        logined_user = session.query(UserLogin).filter(UserLogin.uid == uid).first()
        if logined_user:
            session.delete(logined_user)
            logout_user = session.query(User).filter(User.uid == uid).first()
            logout_user.last_offline_time = datetime.datetime.now()
            session.commit()
            session.close()
            return True
        else:
            session.close()
            return False

    def run(self):
        """
        服务器启动
        :return: none
        """
        self.__socket.bind(('127.0.0.1', 8888))
        self.__socket.listen(10)
        print('[SERVER] The Server is running...')

        while True:
            connection, address = self.__socket.accept()
            print('\033[1;33;33m[Server]\033[0m 收到一个新连接', connection.getsockname(), connection.fileno())
            try:
                buffer = connection.recv(1024).decode()
                obj = json.loads(buffer)
                print(obj)
                if obj['type'] == 'register':
                    new_user_uid = self.__create_user(obj['nickname'], obj['password'])
                    connection.send(json.dumps({
                        'type': 'info',
                        'uid': new_user_uid,
                        'status': 'success'
                    }).encode())
                elif obj['type'] == 'login':
                    login_user = self.__user_login(obj['uid'], obj['password'], obj['ip_address'])
                    if login_user is not False:
                        self.__connections[int(obj['uid'])] = connection
                        connection.send(json.dumps({
                            'type': 'info',
                            'uid': obj['uid'],
                            'nickname': login_user,
                            'status': 'success'
                        }).encode())
                        thread = threading.Thread(target=self.__user_thread, args=(int(obj['uid']),))
                        thread.setDaemon(True)
                        thread.start()

                    else:
                        connection.send(json.dumps({
                            'type': 'info',
                            'uid': obj['uid'],
                            'status': 'failed'
                        }).encode())

                else:
                    print('\033[1;33;33m[Server]\033[0m 无法解析json数据包:', connection.getsockname(), connection.fileno())
            except Exception as e:
                print(e)
                print('\033[1;33;33m[Server]\033[0m 无法接受数据:', connection.getsockname(), connection.fileno())

        # print(self.__create_user('ying8rui', 'ying8rui'))
