from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import make_response
from flask import abort

import uuid

from models import User
from models import Tweet


app = Flask(__name__)

cookie_dict = {}


# 通过 session 来获取当前登录的用户
def current_user():
    cid = request.cookies.get('cookie_id')
    user = cookie_dict.get(cid, None)
    return user

# 注册根目录，返回登录页面
@app.route('/')
def index():
    return redirect(url_for('login_view'))


# 显示登录界面的函数  GET
@app.route('/login')
def login_view():
    return render_template('login.html')


# 处理登录请求  POST
@app.route('/login', methods=['POST'])
def login():
    u = User(request.form)
    user = User.query.filter_by(username=u.username).first()
    print(user)
    if user.validate(u):
        print("用户登录成功")
        # 用 make_response 生成响应 并且设置 cookie
        r = make_response(redirect(url_for('timeline_view', username=user.username)))
        cookie_id = str(uuid.uuid4())
        cookie_dict[cookie_id] = user
        r.set_cookie('cookie_id', cookie_id)
        return r
    else:
        print("用户登录失败", user)
        return redirect(url_for('login_view'))


# 处理注册的请求  POST
@app.route('/register', methods=['POST'])
def register():
    u = User(request.form)
    if u.valid():
        print("用户注册成功")
        # 保存到数据库
        u.save()
        return redirect(url_for('login_view'))
    else:
        print('注册失败', request.form)
        return redirect(url_for('login_view'))


# 显示某个用户的时间线  GET
@app.route('/timeline/<username>')
def timeline_view(username):
    # 查找 username 对应的用户
    # 对查询对象调用 str 方法，可以知道它执行的 sql 语句
    # str(a) 相当于 a.__str__()
    # sql = str(User.query.filter_by(username=username))
    # print(sql)
    # first() 取第一个数据，其他方法我们以资料的形式提供
    u = User.query.filter_by(username=username).first()
    if u is None:
        # 找不到就返回 404, 这是 flask 的默认 404 用法
        abort(404)
    else:
        # 找到就查找这个用户的所有微博并且逆序排序返回
        # sort 函数的用法 再解释
        # tweets = Tweet.query.filter_by(user_id=u.id).all()
        # 
        # lambda 就是匿名函数的意思
        # lambda t: t.created_time
        # 上面的匿名函数相当于下面这个函数
        # def func(t):
        #     return t.created_time
        tweets = u.tweets
        tweets.sort(key=lambda t: t.created_time, reverse=True)
        return render_template('timeline.html', tweets=tweets, user=current_user())


# 处理 发送 微博的函数  POST
@app.route('/tweet/add', methods=['POST'])
def tweet_add():
    user = current_user()
    if user is None:
        return redirect(url_for('login_view'))
    else:
        t = Tweet(request.form)
        # 设置是谁发的
        t.user = user
        # 保存到数据库
        t.save()
        return redirect(url_for('timeline_view', username=user.username))


# 显示 更新 微博的界面
@app.route('/tweet/update/<tweet_id>')
def tweet_update_view(tweet_id):
    t = Tweet.query.filter_by(id=tweet_id).first()
    if t is None:
        abort(404)
    # 获取当前登录的用户, 如果用户没登录或者用户不是这条微博的主人, 就返回 401 错误
    user = current_user()
    if user is None or user.id != t.user_id:
        abort(401)
    else:
        return render_template('tweet_edit.html', tweet=t)


# 处理 更新 微博的请求
@app.route('/tweet/update/<tweet_id>', methods=['POST'])
def tweet_update(tweet_id):
    t = Tweet.query.filter_by(id=tweet_id).first()
    if t is None:
        abort(404)
    # 获取当前登录的用户, 如果用户没登录或者用户不是这条微博的主人, 就返回 401 错误
    user = current_user()
    if user is None or user.id != t.user_id:
        abort(401)
    else:
        t.content = request.form.get('content', '')
        t.save()
        return redirect(url_for('timeline_view', username=user.username))


# 处理 删除 微博的请求
@app.route('/tweet/delete/<tweet_id>')
def tweet_delete(tweet_id):
    t = Tweet.query.filter_by(id=tweet_id).first()
    if t is None:
        abort(404)
    # 获取当前登录的用户, 如果用户没登录或者用户不是这条微博的主人, 就返回 401 错误
    user = current_user()
    if user is None or user.id != t.user_id:
        abort(401)
    else:
        t.delete()
        return redirect(url_for('timeline_view', username=user.username))

# 作业3
# 添加一个管理路由, 地址为 /admin/users
# 显示所有的用户, 想显示多少信息随意, 至少要有 id username role

# 作业三主代码代实现如下：
# 查找并显示所有用户的id，用户名，角色，密码属性
# 定义一个html网页用来显示查询出的所有用户
@app.route('/admin/users/')
def show_users():
    users = User.query.all()
    if users is None:
        abort(404)
    else:
        return render_template('admin_view_allusers.html', users = users)


# 作业4
# 在作业 3 的页面里添加一个删除用户的链接
# 添加一个 /admin/users/delete/<user_id> 处理删除用户
#
# 作业四代码实现如下 ：
# 在User数据库中定义delete方法
# 删除后重定向到显示页面
@app.route('/admin/users/delete/<user_id>')
def users_delete(user_id):
    u = User.query.filter_by(id=user_id).first()
    #作业5
    #在作业4的删除用户的函数里面添加一个权限验证
    #如果当前登录用户的role是1(管理员)则删除否则返回401错误'''
    #
    # 代码如下：
    # 获取当前用户，检测是否管理员
    user = current_user()
    if user.role != 1:
        abort(401)
    else:
        u.delete()
        return redirect(url_for('show_users'))

# 作业6
# 在作业 3 的页面里添加一个编辑用户的链接
# 路由为 /admin/users/update/<user_id>
# 和发微博的路由处理一样 GET 显示页面 POST 更新数据 在这里面管理员(作业5)可以修改用户的密码
#
# 定义修改密码页面，并判断当前用户是否管理员
# 有权限则渲染密码修改页面
@app.route('/admin/users/update/<user_id>')
def users_update_view(user_id):
    u = User.query.filter_by(id=user_id).first()
    if u is None:
        abort(404)
    # 获取当前登录的用户, 如果用户没登录或者用户不是管理员, 就返回 401 错误
    user = current_user()
    if user is None or user.role !=1 :
        abort(401)
    else:
        return render_template('revise_password.html', u = u)

# 获取新密码并保存， 展示
@app.route('/admin/users/update/<user_id>', methods=['POST'] )
def update_user_password(user_id):
    print(user_id)
    u = User.query.filter_by(id=user_id).first()
    print(u)
    if u is None:
        abort(404)
    user = current_user()
    if user is None or user.id != 1:
        abort(401)
    else:
        u.password = request.form.get('password', '')
        u.save()
        return redirect(url_for('show_users'))


if __name__ == '__main__':
    # 162.243.139.166
    #host, port = '162.243.139.166', 14005
    args = {
        #'host': host,
        #'port': port,
        'debug': True,
    }
    app.run(**args)

# 数据库有个功能叫做索引
# 索引就是一个 字段：id 的字典
# 这样你就能够通过 字段 查找到 id
# 然后实现 O(1) 的快速查询