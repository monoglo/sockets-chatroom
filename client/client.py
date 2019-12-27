import datetime
import socket
import threading
import json
from cmd import Cmd


class Client(Cmd):
    """
    客户端
    """
    prompt = ''
    intro = '[Welcome] 简易聊天室客户端(Cli版)\n' + '[Welcome] 输入help来获取帮助\n'

    def __init__(self):
        """
        构造
        """
        super().__init__()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__uid = None
        self.__nickname = None

    def __receive_message_thread(self):
        """
        接受消息线程
        """
        while True:
            # noinspection PyBroadException
            try:
                buffer = self.__socket.recv(1024).decode()
                print('\033[1;35m[SOCKET]\033[0m' + buffer)
                obj = json.loads(buffer)
                print(obj)
                if obj['type'] == 'message':
                    if obj['receiver_uid']:
                        print('[' + str(obj['sender_nickname']) + '(' + str(obj['sender_uid']) + ')' + ']',
                              obj['message'])
                    elif obj['group_gid']:
                        print('[' + str(obj['group_name']) + ']' + '[' + str(obj['sender_nickname']) + '(' + str(
                            obj['sender_uid']) + ')' + ']',
                              obj['message'])
            except Exception:
                print('[Client] 无法从服务器获取数据')
                return 0

    def __send_message_thread(self, message):
        """
        发送消息线程
        :param message: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'message',
            'sender_uid': self.__uid,
            'sender_ip': socket.gethostbyname(socket.gethostname()),
            'receiver_uid': '102',
            'message': message,
            'group_gid': '',
            'create_time': str(datetime.datetime.now())
        }).encode())

    def __group_send_message_thread(self, group_gid, message):
        """
        发送消息线程
        :param message: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'message',
            'sender_uid': self.__uid,
            'sender_ip': socket.gethostbyname(socket.gethostname()),
            'receiver_uid': '',
            'message': message,
            'group_gid': group_gid,
            'create_time': str(datetime.datetime.now())
        }).encode())

    def __create_group_thread(self, group_name):
        """
        发送创建组线程
        :param group_name: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'group',
            'action': 'create',
            'creater_uid': self.__uid,
            'creater_ip': socket.gethostbyname(socket.gethostname()),
            'group_name': group_name,
            'create_time': str(datetime.datetime.now())
        }).encode())

    def __join_group_thread(self, group_gid):
        self.__socket.send(json.dumps({
            'type': 'group',
            'action': 'join',
            'group_gid': group_gid,
            'uid': self.__uid,
        }).encode())

    def start(self):
        """
        启动客户端
        """
        self.cmdloop()

    def do_login(self, args):
        """
        登录聊天室
        :param args: 参数
        """
        uid = args.split(' ')[0]
        password = args.split(' ')[1]
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.connect(('127.0.0.1', 8888))
        # 将昵称发送给服务器，获取用户uid
        self.__socket.send(json.dumps({
            'type': 'login',
            'uid': uid,
            'password': password,
            'ip_address': socket.gethostbyname(socket.gethostname())
        }).encode())
        # 尝试接受数据m
        # noinspection PyBroadException
        try:
            print('等待中。。。')
            buffer = self.__socket.recv(1024).decode()
            obj = json.loads(buffer)
            if obj['type'] == 'info':
                if obj['status'] == 'success':
                    print('[Client] 成功登录到聊天室')
                    self.__uid = obj['uid']
                    self.__nickname = obj['nickname']
                    # 开启子线程用于接受数据
                    thread = threading.Thread(target=self.__receive_message_thread)
                    thread.setDaemon(True)
                    thread.start()
                else:
                    print('登陆失败')
                    self.__socket.close()
            else:
                print('[Client] 无法登录到聊天室')
        except Exception:
            print('[Client] 无法从服务器获取数据')

    def do_register(self, args):
        """
        注册账户
        :param args: 参数
        """
        nickname = args.split(' ')[0]
        password = args.split(' ')[1]
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.connect(('127.0.0.1', 8888))
        # 将昵称发送给服务器，获取用户uid
        self.__socket.send(json.dumps({
            'type': 'register',
            'nickname': nickname,
            'password': password,
        }).encode())
        # 尝试接受数据m
        # noinspection PyBroadException
        try:
            print('等待中。。。')
            buffer = self.__socket.recv(1024).decode()
            obj = json.loads(buffer)
            if obj['type'] == 'info':
                if obj['status'] == 'success':
                    print('[Client] 注册成功')
                    print('[Server] 注册uid为：' + str(obj['uid']))
                    self.__socket.close()
                else:
                    print('注册失败')
                    self.__socket.close()
            else:
                print('[Client] 无法连接到聊天室')
        except Exception as e:
            print(e)

    def do_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        message = args
        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__uid) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__send_message_thread, args=(message,))
        thread.setDaemon(True)
        thread.start()

    def do_group_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        # TODO 若不在群组中返回发送错误
        group_gid = args.split(' ')[0]
        message = args.split(' ')[1]
        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__uid) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__group_send_message_thread, args=(group_gid, message,))
        thread.setDaemon(True)
        thread.start()

    def do_create_group(self, args):
        group_name = args.split(' ')[0]
        thread = threading.Thread(target=self.__create_group_thread, args=(group_name,))
        thread.setDaemon(True)
        thread.start()

    def do_join_group(self, args):
        group_gid = args.split(' ')[0]
        thread = threading.Thread(target=self.__join_group_thread, args=(group_gid,))
        thread.setDaemon(True)
        thread.start()

    def do_help(self, arg):
        """
        帮助
        :param arg: 参数
        """
        command = arg.split(' ')[0]
        if command == '':
            print('[Help] register nickname password - 登录到聊天室，nickname是你选择的昵称，password是你的密码')
            print('[Help] login uid password - 登录到聊天室，uid是你的账户id，password是你的密码')
            print('[Help] send message - 发送消息，message是你输入的消息')
            print('[Help] group_send message - 群消息，message是你输入的消息')
            print('[Help] create_group group_name - 创建群组，group_name是你要创建的群组名')
            print('[Help] join_group group_gid - 加入群组，group_gid是你要加入的群组id')
        elif command == 'register':
            print('[Help] register nickname password - 登录到聊天室，nickname是你选择的昵称，password是你的密码')
        elif command == 'login':
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
        elif command == 'send':
            print('[Help] send message - 发送消息，message是你输入的消息')
        elif command == 'group_send':
            print('[Help] group_send message - 发送群消息，message是你输入的消息')
        elif command == 'create_group':
            print('[Help] create_group group_name - 创建群组，group_name是你要创建的群组名')
        elif command == 'join_group':
            print('[Help] join_group group_gid - 加入群组，group_gid是你要加入的群组id')
        else:
            print('[Help] 没有查询到你想要了解的指令')
