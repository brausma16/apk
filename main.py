# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
import requests
import json
import random
import time
from datetime import datetime, timedelta
import os

# Define your main layout
class MainLayout(BoxLayout):
    # Define the UI elements using ObjectProperty
    user_id_input = ObjectProperty()
    user_name_input = ObjectProperty()

    # Function to handle button click
    def start(self):
        user_id = self.user_id_input.text
        user_name = self.user_name_input.text

        # Your logic goes here
        if user_id in user_data and datetime.strptime(user_data[user_id]["expiration_date"], "%Y-%m-%d %H:%M:%S") > datetime.now():
            expiration_date = datetime.strptime(user_data[user_id]["expiration_date"], "%Y-%m-%d %H:%M:%S")
            time_left = expiration_date - datetime.now()
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            send_welcome_message(user_name, days, hours, minutes)
            print("🙌 مرحبا في بوت انيس 😊")
            print("يرجى إرسال رقمك يوز لمواصلة العملية")
            get_mobile_number()
        else:
            send_notification_message(user_name)


def get_mobile_number():
    mobile_number = input("الرجاء إدخال رقم الهاتف: ")

    url = "https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "client_id": "ibiza-app",
        "grant_type": "password",
        "mobile-number": mobile_number,
        "language": "AR"
    }
    response = requests.post(url, headers=headers, data=payload)

    if "ROOGY" in response.text:
        otp = input("✅ تم إرسال رمز التحقق إلى جوالك. الرجاء إدخال رمز التحقق: ")
        verify_otp(otp, mobile_number)
    else:
        print("❌ فشل في إرسال رمز التحقق. الرجاء المحاولة مرة أخرى.")

def verify_otp(otp, mobile_number):
    url = "https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "client_id": "ibiza-app",
        "grant_type": "password",
        "mobile-number": mobile_number,
        "language": "AR",
        "otp": otp
    }
    response = requests.post(url, headers=headers, data=payload)
    access_token = response.json().get("access_token")

    if access_token:
        initial_bundle_balance = fetch_bundle_balance(access_token)
        send_bundle_balance_info(initial_bundle_balance, before_apply=True)  # Send initial bundle balance before applying MGM
        time.sleep(1.5)  # Wait for 3 seconds before applying MGM numbers
        apply_mgm_number(access_token)
    else:
        print("❌ فشل التحقق من رمز.")

def apply_mgm_number(access_token):
    invited_user_number = []

    for _ in range(6):
        invited_number = "05" + str(random.randint(1000000000, 9999999999))
        invited_user_number.append(invited_number)

    success_message_sent = False

    for number in invited_user_number:
        url = ADD_MGM_DASHBOARD

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "skipMgm": True,
            "mgmValue": "50",
            "referralCode": number
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200 and not success_message_sent:
                response_json = response.json()
                show_won_popup = response_json.get("showWonPopUp", False)
                if show_won_popup:
                    print("✅ تم  ارسال الانترنت بنجاح!")
                    time.sleep(1.5)
                    success_message_sent = True
            elif response.status_code != 200:
                print("❌ لم تتم العملية بنجاح، الرجاء المحاولة بعد 2 دقائق")

            time.sleep(0.5)

        except Exception as e:
            print(e)
            
    if success_message_sent:
        # Fetch updated bundle balance
        updated_bundle_balance = fetch_bundle_balance(access_token)
        send_bundle_balance_info(updated_bundle_balance, before_apply=False)  # Send updated bundle balance after applying MGM

def fetch_bundle_balance(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(GET_USER_BUNDLE_BALANCE, headers=headers)
    if response.status_code == 200:
        bundle_balance = response.json()
        for account in bundle_balance.get('accounts', []):
            if account.get('accountName') == 'BonusDataMGMAccountID':
                return account.get('value'), account.get('validation')
    return None, None

def send_bundle_balance_info(bundle_balance_info, before_apply=True):
    value, validation = bundle_balance_info
    if before_apply:
        print(f"رصيد التكفل المهدى قبل العملية: {value}🌐")
        print(f"التاريخ الصلاحية: {validation} 📊")
    else:
        print(f"رصيد التكفل المهدى بعد العملية: {value}🌐")
        print(f"التاريخ الصلاحية: {validation} 🔄")

# Define the app class
class MyKivyApp(App):
    def build(self):
        return MainLayout()
