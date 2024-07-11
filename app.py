from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import logging
import uuid
import os
import platform

app = Flask(__name__)

# Path to the logs directory
logs_dir = "logs"
app_log = os.path.join(logs_dir, 'app.log')
allow_log = os.path.join(logs_dir, 'allow.log')
deny_log = os.path.join(logs_dir, 'deny.log')

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 配置日志记录
logging.basicConfig(filename=app_log, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s ### : %(message)s')

# 创建自定义日志器
logger1 = logging.getLogger('logger1')
logger2 = logging.getLogger('logger2')

# 设置日志级别
logger1.setLevel(logging.DEBUG)
logger2.setLevel(logging.DEBUG)

# 创建处理器
file_handler1 = logging.FileHandler(allow_log)
file_handler2 = logging.FileHandler(deny_log)

# 创建格式器并添加到处理器
formatter1 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter2 = logging.Formatter('%(asctime)s : %(message)s')
file_handler1.setFormatter(formatter1)
file_handler2.setFormatter(formatter2)

# 将处理器添加到日志器
logger1.addHandler(file_handler1)
logger2.addHandler(file_handler2)


# 用户demo数据，请换成自己的用户数据源
users = {
    "admin": "nzDrdSKN9JS5IGhZkwxs",
    "user": "HIAExuX81QWw4KyM8P3W"
}

ipset_name = 'allow001'


def ipset_init():
    ret = os.system('ipset list -n ' + ipset_name)
    if ret == 0:
        return
    else:
        os.system('ipset create ' + ipset_name + ' hash:net')
        os.system('iptables -I INPUT -m set --match-set ' + ipset_name + ' src -j ACCEPT')


def firewall_allow_win():
    generated_uuid = uuid.uuid4()
    rule_name = 'z-allow-' + str(generated_uuid)[:8]
    cmd = 'netsh advfirewall firewall add rule name='
    cmd += rule_name
    cmd += ' dir=in action=allow localip=any remoteip='
    cmd += request.remote_addr
    os.system(cmd)


def firewall_allow_linux():
    ipset_init()
    cmd = 'ipset add ' + ipset_name + ' '
    cmd += request.remote_addr
    os.system(cmd)


@app.route('/')
def home():
    app.logger.info('Home page accessed')
    user_ip = request.remote_addr
    app.logger.info(f'Access IP: {user_ip}')
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user_ip = request.remote_addr
    app.logger.debug(f'Attempted login with username: {username}')
    if username in users and users[username] == password:
        app.logger.info(f'User {username} logged in successfully')
        app.logger.info(f'AllowIP: {user_ip}')
        logger1.debug(f'AllowRecord : {user_ip}|\"{username}\"|\"{password}\"')
        if platform.system() == 'Windows':
            firewall_allow_win()
        else:
            firewall_allow_linux()
        return redirect(url_for('success'))
    else:
        app.logger.warning(f'Failed login attempt for: \"{username}|{password}\"')
        logger2.debug(f'DenyRecord : {user_ip}|\"{username}\"|\"{password}\"')
        return redirect(url_for('failure'))


@app.route('/success')
def success():
    app.logger.info('Login success page accessed')
    return "登录成功！"


@app.route('/failure')
def failure():
    app.logger.info('Login failure page accessed')
    return "登录失败，用户名或密码错误。"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=80)
