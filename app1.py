from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from cmail import sendmail
import random
from bid import  genotp1
import os
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
app=Flask(__name__)
app.secret_key='*c123x1@5ds'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='sns'
Session(app)
mysql=MySQL(app)
@app.route('/index')
def home():
    return render_template('index.html')
@app.route('/signup',methods=['GET','POST'])
def signup(): 
    if request.method=='POST':
        email=request.form['email']
        username=request.form['username']
        password=request.form['password']    
        cursor=mysql.connection.cursor()
        cursor.execute('select email from users')
        data=cursor.fetchall()
        cursor.execute('SELECT username from users')
        edata=cursor.fetchall()
        #print(data)
        if (email,) in data:
            flash('Email Id (or) Username already exists')
            return render_template('signup.html')
        if (username,) in edata:
            flash('username already already exists')
            return render_template('signup.html')
        cursor.close()
        otp=genotp()        
        subject='Thanks for registering to the application '
        body=f'Use this otp to signup {otp}'
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,email=email,username=username,password=password)
    return render_template('signup.html')


@app.route('/login',methods=['GET','POST']) 
def login():
    if session.get('user'):
        return redirect((url_for('homepage')))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid password or username')
            return render_template('login.html')
        else:
            session['user']=username
            return redirect(url_for('homepage'))
    return render_template('login.html')  
@app.route('/otp/<otp>/<email>/<username>/<password>',methods=['GET','POST'])
def otp(otp,email,username,password):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            cursor.execute('insert into users values(%s,%s,%s)',(email,username,password))
            mysql.connection.commit()
            cursor.close()
            flash('details registered')
            return redirect(url_for('login'))
        else:
            flash('wrong otp')
            return render_template('otp.html',otp=otp,email=email,username=username,password=password)
@app.route('/homepage')
def homepage():
        if session.get('user'):
            cursor=mysql.connection.cursor()
            cursor.execute('select * from post order by date desc ')
            data=cursor.fetchall()
            cursor.close()
            return render_template('homepage.html',data=data)
        else:
            return redirect(url_for('login'))
@app.route('/yourprofile')
def yourprofile():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from post where username=%s  order by date desc',[session.get('user')])
        data=cursor.fetchall()
        cursor.close()
        return render_template('yourprofile.html',data=data)
    else:
        return render_template(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
@app.route('/createpost', methods=['GET','POST'])
def createpost():
    if session.get('user'):
        if request.method=='POST':
            description=request.form['description']
            image=request.files['image']
            filename=image.filename.split('.')[-1]
            if filename!='jpg':
                #need change
                #flash('wrong input file')
                #return render_template('createpost.html')
                return 'wrong input file'
            caption=request.form['caption']
            cursor=mysql.connection.cursor()
            username=session.get('user')
            pid=genotp1()
            path=r"C:\Users\tatip\sns\static"
            filepath=pid+'.jpg'
            img_path=os.path.join(path,filepath)
            image.save(img_path)
            cursor.execute('insert into post(pid,username,description,caption) values(%s,%s,%s,%s)',[pid,username,description,caption])
            mysql.connection.commit()
            cursor.close() 
            flash('f{username} added your post successfully')
        return render_template('createpost.html')
    else:
        return redirect(url_for('login'))

    

@app.route('/deletepost/<pid>')
def deletepost(pid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from post where pid=%s',[pid])
    mysql.connection.commit()
    cursor.close
    flash('post deleted successfully')
    return redirect(url_for('yourprofile'))

@app.route('/page/<pid>')
def page(pid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from post where pid=%s',[pid])
        data=cursor.fetchall()
        cursor.close()
        return render_template('page.html',data=data)
    else:
        return redirect(url_for('login'))

@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=="POST":
        username=request.form['search']
        cursor=mysql.connection.cursor()
        cursor.execute('select * from post where username=%s',[username])
        data=cursor.fetchall()
        return render_template('homepage.html',data=data)


@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        username=request.form['username']
        cursor=mysql.connection.cursor()
        cursor.execute('select username from users')
        data=cursor.fetchall()
        if (username,) in data:
            cursor.execute('select email from users where username=%s',[username])
            data=cursor.fetchone() [0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("createpassword",token=token(username,240))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('forgotpassword.html')

@app.route('/newpassword/<token>',methods=['GET','POST'])
def newpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        username=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update users set password=%s where username=%s',[npass,username])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except: 
        return 'Link expired try again'      
    
    
    


app.run(debug=True,use_reloader=True)
