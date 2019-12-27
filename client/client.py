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
            except Exception:
                print('[Client] 无法从服务器获取数据')

    def __send_message_thread(self, message):
        """
        发送消息线程
        :param message: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'message',
            'sender_uid': self.__uid,
            'sender_ip': '127.0.0.1',
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
            'sender_ip': '127.0.0.1',
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
            'creater_ip': '127.0.0.1',
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
            'ip_address': '127.0.0.1'
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

    def do_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        message = args
        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__uid) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__send_message_thread, args=(message, ))
        thread.setDaemon(True)
        thread.start()

    def do_group_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        group_gid = args.split(' ')[0]
        message = args
        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__uid) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__group_send_message_thread, args=(group_gid, message, ))
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
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
            print('[Help] send message - 发送消息，message是你输入的消息')
        elif command == 'login':
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
        elif command == 'send':
            print('[Help] send message - 发送消息，message是你输入的消息')
        else:
            print('[Help] 没有查询到你想要了解的指令')


