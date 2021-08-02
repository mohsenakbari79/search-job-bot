
from requests import Session
from bs4 import BeautifulSoup as bs
from telebot import types
import re
import psycopg2
import telebot 
import time
import threading
from decouple import config
from flask import Flask, request
import os
import urllib.parse as urlparse


# forbot
bot = telebot.TeleBot("1687745431:AAHVE7SVaGhI3JrMIZbsT5qrJ2wWoOjQVKE")
TOKEN = '1687745431:AAHVE7SVaGhI3JrMIZbsT5qrJ2wWoOjQVKE'
tb = telebot.TeleBot(TOKEN)



server = Flask(__name__)

class dbClass:
    def  __init__(self):
        self.conn =psycopg2.connect(
            database=config('DATABASE_NAME'),
            user=config('USER_DB'),
            password=config('PASSWORD_DB'),
            host=config('HOST_DB'),
            port=config("PORT_DB")
        )
            
        self.cur = self.conn.cursor()

class Jobinja:
    def __init__(self):
        with Session() as s:
            self.s=s
            self.headers ={
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0"
            }
            site = self.s.get("https://jobinja.ir/login/user",headers=self.headers)
            bs_content = bs(site.content, "html5lib")
            token = bs_content.find('input', {"name": "r"})
            
            if not bool(token):
                token = bs_content.find('input', {"name": "_token"})
            token = token["value"]
            login_data = {

                            "identifier":config('JOBINJA_USER'),
                            "password":config('JOBINJA_PASS'),
                            "_token":token,
                            "remember_me":"on",
                            }
            self.s.post("https://jobinja.ir/login/user",login_data,headers=self.headers)


            main_page=self.s.get("https://jobinja.ir/jobs",headers=self.headers)
            self.maincontent = bs(main_page.content, "html5lib")
    
    def __alljobs(self):
        all_job = self.maincontent.find("ul", {"id": "jobsCategoriesFilters"})
        all_job = all_job.find_all("span", {"class": "c-jobSearch__subListText"})
        self.all_job =[m.text for m in all_job]
        return self.all_job
    def __allcity(self):
        all_city = self.maincontent.find("ul", {"id": "jobsStatesFilters"})
        all_city = all_city.find_all("span", {"class": "c-jobSearch__subListText"})
        self.all_city =[m.text for m in all_city]
        return self.all_city
    # def timeworker(self):
    #     timing = self.maincontent.find("ul", {"id": "jobSearchSide__subListWrapper"})
    #     timing = timing.find_all("span", {"class": "c-jobSearch__subListText"})
    #     self.timing =[m.text.replace(" ", "+") for m in timing]
    #     return self.timing
    def get_contect(self,job="",city="",page=1):
        url="https://jobinja.ir/jobs?filters[keywords][0]=&filters[keywords][0]=&filters[job_categories][0]="+job+"&filters[locations][0]="+city+"&sort_by=relevance_desc"+"&page="+str(page)
        main_page=self.s.get("https://jobinja.ir/jobs",headers=self.headers)
        main_page = bs(main_page.content, "html5lib")
        contents = main_page.find_all("div", {"class": "o-listView__itemInfo"})
        all_contect=[]
        for content in contents:
            temp=[]
            temp.append(content.find('a', {"class": "o-listView__itemIndicator o-listView__itemIndicator--noPaddingBox"})["href"])
            temp.append(content.find('img', {"class": "o-listView__itemIndicatorImage"})["src"])
            temp.append(content.find('a', {"class": "c-jobListView__titleLink"}).text)
            spans=content.find_all("span")
            temp_span=[]
            for span in spans:
                temp_span.append(re.sub('\s+',' ',span.text))
            temp.append(temp_span)
            all_contect.append(temp)
        self.content=all_contect
        return self.content
    def start_get_jobinja_job(self,message):
        markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        chat_id= message.chat.id
        jobs=self.__alljobs()
        for i in range(0,len(jobs),3):
            if i+2<len(jobs):
                itembtn1 = types.KeyboardButton(jobs[i])
                itembtn2 = types.KeyboardButton(jobs[i+1])
                itembtn3 = types.KeyboardButton(jobs[i+2])
            elif i+1<len(jobs):
                itembtn1 = types.KeyboardButton(jobs[i])
                itembtn2 = types.KeyboardButton(jobs[i+1])
            elif i<len(jobs):
                itembtn1 = types.KeyboardButton(jobs[i])
            else:
                break
            markup.add(itembtn1,itembtn2,itembtn3)
        msg=bot.send_message(chat_id, "رشته مورد نظر خود را وارد کنید", reply_markup=markup)
        bot.register_next_step_handler(msg,self.get_jobinja_city)
    def get_jobinja_city(self,message):
        city=self.__allcity()
        markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        chat_id= message.chat.id
        job=message.text
        for i in range(0,len(city),3):
            if i+2<len(city):
                itembtn1 = types.KeyboardButton(city[i])
                itembtn2 = types.KeyboardButton(city[i+1])
                itembtn3 = types.KeyboardButton(city[i+2])
            elif i+1<len(city):
                itembtn1 = types.KeyboardButton(city[i])
                itembtn2 = types.KeyboardButton(city[i+1])
            elif i<len(city):
                itembtn1 = types.KeyboardButton(city[i])
            else:
                break
            markup.add(itembtn1,itembtn2,itembtn3)
        msg=bot.send_message(chat_id, "شهر مورد نظر خود را وارد کنید", reply_markup=markup)
        bot.register_next_step_handler(msg,self.savecity,job)
    def savecity(self,message,job):
        try:
            self.db=dbClass()
            city=message.text
            print(message)
            # contects= self.get_contect(job,city)
            self.db.cur.execute("select * from jobinja where username=%s", (message.chat.username,))
            result= self.db.cur.fetchone()
            if bool(result):
                self.db.cur.execute("UPDATE jobinja SET job=%s,city=%s WHERE username=%s;",(job,city,message.chat.username))
            else:
                self.db.cur.execute("INSERT INTO jobinja (username,job,city) VALUES (%s,%s,%s);",(message.chat.username,job,city))
            Sucssess=True
        except:
            self.db.conn.rollback()
            Sucssess=False
        finally:
            self.db.conn.commit()
            self.db.conn.close()
            if Sucssess:
                bot.send_message(message.chat.id, "با موفقیت ذخیره شد")
            else:
                bot.send_message(message.chat.id, "مشکلی در ذخیره داده وجود داشت لطفا در فرصتی دیگر امتحان کنید", )
            user.menu(message)

        
        

    
    # def send_welcome(message):
    #     markup = types.ReplyKeyboardMarkup(row_width=3)
    #     chat_id= message.chat.id
    #     jobs=webfirst.alljobs()
        

class User:
    def __init__(self):
        self.db=dbClass()
        self.jobinja=Jobinja()
    def __del__(self):
        self.db.conn.close() 
    def jobinja_chack(self):
        self.db.cur.execute("select * from jobinja  where username=%s", (self.username,))
        result= self.db.cur.fetchone()
        print(result)
        return bool(result)
    def user_check_exit(self):
        self.db.cur.execute("select * from botuser  where username=%s", (self.username,))
        result= self.db.cur.fetchone()
        print(result)
        return bool(result)
    def menu(self,message):
        self.username=message.chat.username
        self.chatid=message.chat.id
        self.first_name=message.chat.first_name
        self.last_name=message.chat.last_name
        if not self.user_check_exit():
            try:
                self.db.cur.execute("INSERT INTO botuser (username,chat_id,firstname,lastname) VALUES (%s,%s,%s,%s);",(self.username,self.chatid,self.first_name,self.last_name))
                print("save true")
            except:
                self.db.conn.rollback()
                print("problem4")
            finally:
                self.db.conn.commit()
                
        

        markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        itembtn1 = types.KeyboardButton('تنظیمات جابینجا')
        itembtn2 = types.KeyboardButton('تنظیمات پونیشا')
        itembtn3 = types.KeyboardButton('تنظیمات کاربری')
        itembtn4 = types.KeyboardButton('خروج')
        markup.add(itembtn1,itembtn2)
        markup.add(itembtn3)
        markup.add(itembtn4)

        msg=bot.send_message(self.chatid, "گزینه مورد نظر خود را وارد کنید", reply_markup=markup)
        bot.register_next_step_handler(msg,self.check_menu)

    
        # return False
    def filters(self):
        result=None
        try:
            print(self.username)
            self.db.cur.execute("select count_filter from botuser where username='{}'".format(self.username))
            result= self.db.cur.fetchone()
        except:
            pass
        markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        itembtn2 = types.KeyboardButton('خروج')
        print(result)
        if bool(result): 
            if int(result[0]) == 10:
                itembtn1 = types.KeyboardButton('ویرایش کردن  فیلتر')
                markup.add(itembtn1,itembtn2)
                msg=bot.send_message(self.chatid, "این رباط محدودیت وارد کردن 10 فیلتر دارد وشما  ده فیلنر خود را وارد کرده اید اکنون با انتخواب ویرایش فیلد جستجو میتوانید فیلد های وارد شده را ویرایش کنید ", reply_markup=markup)
            elif int(result[0])<10:
                itembtn1 = types.KeyboardButton('اضافه کردن فیلتر')
                markup.add(itembtn1,itembtn2)
                msg=bot.send_message(self.chatid, "شما میتوانید فیلد های برای جستجو وارد کرده که در این صورت ربات فقط درخواست های کاری که فیلد های وارد شده توسط شما در مهارت هایش نیاز داشته باشد برای شما مبفرستد ", reply_markup=markup)
            bot.register_next_step_handler(msg,self.checkfiltersadd,result[0])
        else:
            itembtn1 = types.KeyboardButton('اضافه کردن فیلتر')
            markup.add(itembtn1,itembtn2)
            msg=bot.send_message(self.chatid, "شما میتوانید فیلد های برای جستجو وارد کرده که در این صورت ربات فقط درخواست های کاری که فیلد های وارد شده توسط شما در مهارت هایش نیاز داشته باشد برای شما مبفرستد ", reply_markup=markup)
            bot.register_next_step_handler(msg,self.checkfiltersadd)

    def filtersadd(self,message,count):
        Sucssess=None
        if count==None:
            count=0
        if message.text=='/exit' or message.text=='exit':
            self.filters()
            return
        try:
            self.db.cur.execute("INSERT INTO botuser_filter(username,count_filter,filter) VALUES ('{}',{},'{}');".format(message.chat.username,int(count),message.text))
            self.db.cur.execute("UPDATE botuser SET count_filter={}  WHERE username='{}';".format(int(count)+1,message.chat.username))
            Sucssess=True
        except:
            bot.send_message(chat_id=message.chat.id,
                        text='مشکلی پیش امد بعدا امتحان کنید دوباره ')
            self.db.conn.rollback()
        finally:
            self.db.conn.commit()
        if Sucssess==True:
            if count+1<=9:
                echo = bot.send_message(chat_id=message.chat.id,
                        text='با موفقیت ذخیره شد میتوانید مهارتی دیگر نیز اضافه کنید دز صورت عدم تمایل /exit را تایپ کنید ',reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(echo, self.filtersadd,count+1)
            else:
                self.filters()
        else:
            self.filters()
    def filterseditcount(self,message):
        try:
            count=int(message.text)
        except ValueError:
            echo = bot.send_message(chat_id=message.chat.id,
                text="لطفا عدد بین  ‍‍|0_9| وارد کنید داده وارد شده معتبر نمی باشد ",reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message=echo, callback=self.filterseditcount)
            return
        

        if 9<count or count<0:
            echo=bot.send_message(chat_id=message.chat.id,text="شماره اشتباه است|شماره مد نظر برای ادیت را دوباره وارد کنید ")
            bot.register_next_step_handler(message=echo, callback=self.filterseditcount)
        echo = bot.send_message(chat_id=message.chat.id,text="فیلتر مد نظر خود را وارد کنید ")
        bot.register_next_step_handler(echo,self.filtersedit,count)

    def filtersedit(self,message,count):
        filter_text=message.text
        try:
            self.db.cur.execute("UPDATE botuser_filter SET filter='{}' WHERE username='{}' and count_filter={} ;".format(filter_text,self.username,count))
            bot.send_message(chat_id=message.chat.id,text="با موفقیت ذخبره شد")

        except:
            print("problem save filter")
            bot.send_message(chat_id=message.chat.id,text="مشکلی در ذخیره وجود داشت یعدا امتحان کنید")
            self.db.conn.rollback()
        finally:
            self.db.conn.commit() 
        self.menu(message)
    def checkfiltersadd(self,message,count=None):
        if message.text=='خروج':
            self.menu(message)
        elif message.text=='اضافه کردن فیلتر':
            echo = bot.send_message(chat_id=message.chat.id,
                    text='مهارت مورد نظر خود را وارد کنید مثلا : پایتون',reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(echo, self.filtersadd,count)
            
        elif message.text=="ویرایش کردن  فیلتر":
            text="<pre>"
            self.db.cur.execute("select count_filter,filter from botuser_filter  where username='{}'".format(self.username))
            result= self.db.cur.fetchall()
            for x in result:
                text=text+"{}|{} \n".format(str(x[0]),str(x[1]))
            text=text+"</pre>"
            
            bot.send_message(chat_id=message.chat.id,text="شماره مد نظر برای ادیت را وارد کنید ",reply_markup=types.ReplyKeyboardRemove())
            echo = bot.send_message(chat_id=message.chat.id,
                    text=text,parse_mode="html")
            bot.register_next_step_handler(message=echo, callback=self.filterseditcount)
            

        





    def jobinjaadd(self):
        markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        if not self.jobinja_chack():
            itembtn1 = types.KeyboardButton('اضافه کردن فیلد جستجو')
            itembtn2 = types.KeyboardButton("خروج")
            markup.add(itembtn1,itembtn2)
        else:
            itembtn1 = types.KeyboardButton('ویرایش کردن فیلد جستجو')
            itembtn2 = types.KeyboardButton("خروج")
            markup.add(itembtn1,itembtn2)
        msg=bot.send_message(self.chatid, "گزینه مورد نظر خود را وارد کنید", reply_markup=markup)
        bot.register_next_step_handler(msg,self.check_menu_jabinja)
    def check_menu_jabinja(self,message):
        if   message.text=="خروج" :
            self.menu(message) 
        elif message.text=='اضافه کردن فیلد جستجو':
            self.jobinja.start_get_jobinja_job(message)
        elif message.text=='ویرایش کردن فیلد جستجو':
            self.jobinja.start_get_jobinja_job(message)
            
    def check_menu(self,message):
        if   message.text=="تنظیمات جابینجا" :
            self.jobinjaadd() 
        elif message.text=='تنظیمات کاربری':
            self.filters()
        elif message.text=='ویرایش کردن فیلد جستجو':
            pass
            

user=User()
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg=bot.send_message(message.chat.id, "سلام این ربات با هدف سادگی در دنبال کردن درخواست های کار رشته شما ساخته شده است ")
    user.menu(msg)



# check time 
class SendNewPost:
    def __init__(self):
        self.db=dbClass()
        with Session() as s:
            self.s=s
            self.headers ={
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0"
            }
            site = self.s.get("https://jobinja.ir/login/user",headers=self.headers)
            bs_content = bs(site.content, "html5lib")
            token = bs_content.find('input', {"name": "r"})
            if not bool(token):
                token = bs_content.find('input', {"name": "_token"})
            token = token["value"]
            login_data = {
                
                            "identifier":config('JOBINJA_USER'),
                            "password":config('JOBINJA_PASS'),
                            "_token":token,
                            "remember_me":"on",
                            }
            self.s.post("https://jobinja.ir/login/user",login_data,headers=self.headers)


            main_page=self.s.get("https://jobinja.ir/jobs?sort_by=published_at_desc",headers=self.headers)
            self.maincontent = bs(main_page.content, "html5lib") 
    
    
    def __Check_id(self):
        main_page=self.s.get("https://jobinja.ir/jobs?sort_by=published_at_desc",headers=self.headers)
        self.maincontent = bs(main_page.content, "html5lib") 
        self.db.cur.execute(f"select chat_id from IdPost  where onerow_id={True};")
        result= self.db.cur.fetchone()
        print(result)
        try:
            if not bool(result):
                contents = self.maincontent.find("div", {"class": "o-listView__itemWrap c-jobListView__itemWrap u-clearFix"})
                job_id=contents.find('job-fave')["job-short-id"]
                self.db.cur.execute(f"INSERT INTO IdPost (onerow_id,chat_id) VALUES ({True},'{job_id}');")
                result=(job_id,)
            else:
                contents = self.maincontent.find("div", {"class": "o-listView__itemWrap c-jobListView__itemWrap u-clearFix"})
                job_id=contents.find('job-fave')["job-short-id"]
                print("update")
                print(job_id)
                self.db.cur.execute("UPDATE IdPost SET chat_id='{}'  WHERE onerow_id=True;".format(job_id))
            print("save true last post_id")
            return result
        except:
            print("error in save last post id")
            self.db.conn.rollback()
        finally:
            self.db.conn.commit()

    def GetPost(self):
        check_id= self.__Check_id()
        contents= self.maincontent.find_all("div", {"class": "o-listView__itemWrap c-jobListView__itemWrap u-clearFix"})
        AllContect=[]
        for content in contents:
            temp=[]
            temp.append(content.find('job-fave')["job-short-id"])
            temp.append(content.find('a', {"class": "o-listView__itemIndicator o-listView__itemIndicator--noPaddingBox"})["href"])
            print(temp[0]+"|||||||||||||||||||||||"+check_id[0])
            if temp[0]==check_id[0]:
                break
            AllContect.append(temp)
        return AllContect
    def SendPost(self):
        all_contect=self.GetPost()
        listpost=[]
        for contect in all_contect:
            site = self.s.get(contect[1],headers=self.headers)
            bs_content = bs(site.content, "html5lib")
            contents = bs_content.find("section", {"class": "c-jobView o-box o-box--padded u-marginBottom40"})
            contents = contents.find_all("li", {"class": "c-infoBox__item"})
            contect={
                "دسته‌بندی شغلی":None,
                "موقعیت مکانی":None,
                "نوع همکاری":None,
                "حقوق":None,
                "حداقل سابقه کار":None,
                "مهارت‌های مورد نیاز":None,
                "جنسیت":None,
                "وضعیت نظام وظیفه":None,
                "حداقل مدرک تحصیلی":None,
                "آدرس":"<a href='{}'>لینک به سایت</a>".format(contect[1])
                
            }
            for x in contents:
                spans= x.find_all("span", {"class": "black"})
                name= x.find("h4",{"class" : "c-infoBox__itemTitle"})
                temp=''
                for span in spans:
                    temp=temp+span.text.strip().replace("\n","")
                    if len(spans)!=1:
                        temp=temp+"|"
                contect[name.text]=temp
            contect["موقعیت مکانی"]=contect["موقعیت مکانی"].replace(" ","")
            listpost.append(contect)
        return listpost
    def check_Send_Contect(self):
        threading.Timer(600.0, self.check_Send_Contect).start()
        print("start_check")
        posts=self.SendPost()
        for post in posts:
            city = post["موقعیت مکانی"].split("،")
            job = post["دسته‌بندی شغلی"]
            Skill = post["مهارت‌های مورد نیاز"].lower().split("|")
            text=""
            for key,value in post.items():
                if key=="آدرس":
                    text=text+str('<b>{}</b>'.format(value))+"\n"
                    continue
                text=text+str('<b>{}</b>'.format(key))+": "+str('{}'.format(value))+"\n"
            
            self.db.cur.execute("select chat_id,username from botuser where username  in( select username from jobinja where job=%s AND (city=%s OR city=%s))", (job,city[0],city[1]))
            result= self.db.cur.fetchall()
            for user_field in result:
                # print(user_field)
                self.db.cur.execute("select filter from botuser_filter  where username='{}'".format(user_field[1]))
                resultsearchfield = self.db.cur.fetchall()
                print(Skill)
                for field_search in resultsearchfield:
                    print(field_search)
                    if field_search[0].lower() in Skill:
                        print("break")
                        break
                else:
                    print(Skill)
                    continue
                msg=bot.send_message(int(user_field[0]), text,parse_mode="html")
        print("finish_check")



if __name__ == "__main__":
    bot.remove_webhook()
    post=SendNewPost()
    post.check_Send_Contect()
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

bot.polling()


        