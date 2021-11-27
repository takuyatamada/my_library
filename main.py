import password 
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
import time 
from datetime import datetime
import requests

def driver_setup():
    driver = webdriver.Chrome()
    return driver

def login_my_library(driver):
    # driver = webdriver.Chrome()
    login_url = 'https://opac.osakafu-u.ac.jp/opac/opac_search/?loginMode=disp&lang=0&opkey=&cmode=0&smode=0'
    driver.get(login_url)
    user_id = password.USER_ID
    login_pass = password.PASSWORD
    id_elm = driver.find_element_by_id('userid')
    pass_elm = driver.find_element_by_id('p_check_text_pass')
    id_elm.send_keys(user_id)
    pass_elm.send_keys(login_pass)
    login_button_elm = driver.find_element_by_class_name('btn_lead')
    login_button_elm.click()

def access_lending_page(driver):
    #貸し出し状況ページにアクセス
    lending_page = 'https://opac.osakafu-u.ac.jp/opac/odr_stat/?lang=0'
    driver.get(lending_page)

    #表示件数を100件にする
    dropdown =driver.find_element_by_class_name('dataTables_selector')
    select = Select(dropdown)
    select.select_by_value('100')

def check_expand(driver):
    #延長した本のタイトル
    extend_list=[]

    #返却に行かなければいけない本のタイトル
    due_near_list = []
    
    #貸し出し状況が入ったテーブルの要素を指定
    lending_tbody_elm = driver.find_element_by_xpath('/html/body/div[1]/div[5]/div/div/form/div[2]/table/tbody')
    
    #テーブルの各行をtrsにいれる
    trs = lending_tbody_elm.find_elements(By.TAG_NAME, "tr")
    for tr in trs:
        due = tr.find_element_by_xpath("td[@class='nowrap re_rndate']").text
        title = tr.find_element_by_xpath("td[@class='max_width re_title']").text
        
        #check_box_textが空白(' ')なら延長できない
        check_box_text = tr.find_element_by_xpath("td[@class='nowrap re_check']").text
        extend_flag,day_difference = judge_extend(due,title,check_box_text)
        #延長する必要があれば延長ボタンにチェックを入れる
        if extend_flag:
            tr.find_element_by_xpath("td/input").click()
            extend_list.append(title)

        #期限が近付いていて延長もできないほんのタイトルをdue_near_listに追加
        #extend_flagのextend_marginと値を合わせておく
        if extend_flag==False and day_difference<=3:
            due_near_list.append(title)

            
        # print(due,title,check_box_text)

    #一括延長クリック
    bulk_extension_elm = driver.find_element_by_class_name('btn_lead')
    bulk_extension_elm.click()

    return extend_list,due_near_list

def judge_extend(due,title,check_box_text):
    due_datetime = datetime.strptime(due,'%Y.%m.%d')
    now_datetime = datetime.now()
    
    #返却までの日数
    day_difference = (due_datetime - now_datetime).days + 1
    flag = False 
    #check_box_textが空白(' ')なら延長できない
    if check_box_text==' ':
        return flag,day_difference
    #何日前なら延長するのかの決定、3日前にしとくか、、、
    extend_margin = 3
    due_datetime = datetime.strptime(due,'%Y.%m.%d')
    now_datetime = datetime.now()
    day_difference = (due_datetime - now_datetime).days + 1

    #返却までの日数が規定の日にち以下ならflagをTrueにして延長できるようにする
    if day_difference <= extend_margin:
        flag = True 
    return flag,day_difference

def send_line_main(extend_list,due_near_list):
    if len(extend_list)==0 and len(due_near_list)==0:
        return 
    message = '延長した本 \n'
    for extend_title in extend_list:
        message = message + extend_title + '\n\n'
    message = message + 'もうすぐ期限を迎える本 \n\n'
    for due_title in due_near_list:
         message = message + due_title + '\n'
    print(message)
    send_line(message)

def send_line(message):
    #line設定
    url = "https://notify-api.line.me/api/notify"
    access_token = password.ACCESS_TOKEN
    headers = {'Authorization': 'Bearer ' + access_token}
    payload = {'message': message}
    r = requests.post(url, headers=headers, params=payload,)


if __name__ == '__main__':
    driver=driver_setup()
    login_my_library(driver)
    access_lending_page(driver)
    extend_list,due_near_list=check_expand(driver)
    send_line_main(extend_list,due_near_list)
    time.sleep(10)
    driver.close()