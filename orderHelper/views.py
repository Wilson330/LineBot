from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Order, Participant, UserProfile, UserGroup
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage, ImageSendMessage
 
import string
import random

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

reply = {
    "NoExistedOrder": "目前沒有訂單存在，請輸入「發起訂單」來創建新訂單。",
    "NoExistedGroup": "目前無可用群組存在，請創建新群組！",
    "NoExistedMerchandise": "您尚未加入此訂單，請輸入「加入訂單」以添加新的點購。",
    
    "InputNameNGroup": "請依序輸入「會員名稱」及「欲加入之群組」，以下為現有群組。(可以創建新群組，中間請以空格分隔)",
    "InputGroupNShop": "訂單已發起，請先依序輸入「發起群組名稱」和「店家名稱」。(請以空格分隔)",
    "InputMerchandise": "請輸入欲加入的「訂單編號」及欲選購的「品項」、「數量」、「價格」。(請以空格分隔)",
    "InputModifyOrder": "請先輸入欲修改的訂單編號。",
    "InputModifyMerchandise": "請先再次輸入訂單編號，加上欲修改之品項編號以及其他資訊。\n(修改: 1 1 XX商品 1 150\n 刪除: 1 1 刪除)",
    "InputMenu":"請繼續上傳店家菜單(圖片)。",
    
    "ExistedMember": "您的會員已註冊，請輸入「發起訂單」或「加入訂單」來執行操作。",
    "ExistedOrderLimit": "目前訂單已達系統上線，請待訂單結單後再試。",
    
    "SuccessRegistering": "會員註冊完成，請輸入「發起訂單」或「加入訂單」來執行操作。",
    "SuccessRaising": "訂單建立成功，已推播給其他使用者，輸入「訂單內容」以查看當前訂單資訊。",
    "SuccessAdding": "訂單加入成功，輸入「訂單內容」以查看當前訂單資訊。",
    "SuccessModifying": "訂單修改成功，輸入「訂單內容」以查看當前訂單資訊。",
    "SuccessFinishing": "訂單已結單，將顯示最終訂單內容，感謝您的使用。",

    "NotMember": "請先輸入「註冊會員」來開始您的訂購。",
    "NotRaiser": "您並未發起訂單，請輸入「發起訂單」來創建新訂單。",
    "NotInstruction": "查無此指令，請重新輸入！",

    "FailedInput": "輸入錯誤，請重新輸入！",

    "InvalidOrder": "訂單已結束或查無訂單，請重新選擇功能。",

    "ShowInstruction": "「發起訂單」：開啟新的訂單\n「加入訂單」：參與已發起之訂單(一次輸入一筆)\n「修改訂單」：修改您訂購的項目(一次修改一筆)\n「訂單內容」：查詢已加入群組中存在的所有訂單\n「訂單總結」：結束已發起的訂單 (發起人專用)"
    

}

# 註冊會員
def registerMember(user_id, isRegisteredUser):
    if not isRegisteredUser:
        newUser = UserProfile.objects.create(user_id=user_id, userState="registering_state")
        all_user_groups = UserGroup.objects.all()
        if all_user_groups.exists(): 
            group_names = ""
            for group in all_user_groups:
                group_names += "「" + group.__str__() + "」  "
        else:
            group_names = reply["NoExistedGroup"]
        
        return [TextSendMessage(text=reply["InputNameNGroup"]), TextSendMessage(text=group_names)]
    
    else:
        return TextSendMessage(text=reply["ExistedMember"])

# 發起訂單    
def raiseOrder(user_id):
    # 切換用戶狀態
    user = UserProfile.objects.get(user_id=user_id)
    user.userState = 'raising_state'
    user.save()
    
    return TextSendMessage(text=reply["InputGroupNShop"])

# 加入訂單
def addOrder(user_id):
    # 檢查是否存在訂單
    isOrderExists = Order.objects.filter(orderState="existing").exists()
    
    if isOrderExists:
        # 切換用戶狀態
        user = UserProfile.objects.get(user_id=user_id)
        user.userState = 'adding_state'
        user.save()
        
        return TextSendMessage(text=reply["InputMerchandise"])

    else:
        return TextSendMessage(text=reply["NoExistedOrder"])

# 修改訂單
def modifyOrder(user_id):
    # 檢查是否存在訂單
    isOrderExists = Order.objects.filter(orderState="existing").exists()
    
    if isOrderExists:
        # 切換用戶狀態
        user = UserProfile.objects.get(user_id=user_id)
        user.userState = 'modifying_state'
        user.save()
        
        return TextSendMessage(text=reply["InputModifyOrder"])

    else:
        return TextSendMessage(text=reply["NoExistedOrder"])

# 訂單內容查詢
def showOrderStatus(user_id):
    # 顯示已加入群組中存在的所有訂單
    user = UserProfile.objects.get(user_id=user_id)
    groupList = user.groups.all()
    
    retMessage = []
    for group in groupList:
        orderSet = Order.objects.filter(orderState="existing").filter(orderGroupName=group.groupName)
        if orderSet.exists():
            for order in orderSet:
                retMessage.append(TextSendMessage(text=order.__str__())) 
    
    if len(retMessage) > 0:
        return retMessage

    else:
        return TextSendMessage(text=reply["NoExistedOrder"])

# 訂單總結
def finishOrder(user_id):
    # 將訂單關閉並回傳所有資訊給發起者
    orderList = Order.objects.filter(orderState="existing").filter(orderRaiserID=user_id)

    if orderList.exists():
        retMessage = "您發起的訂單如下，請問要結束哪個訂單呢？\n\n"
        for order in orderList:
            retMessage += "訂單編號：{}, 店家名稱：{}\n".format(order.id, order.orderShop)
        retMessage += "\n請輸入欲結束的訂單編號。"

        user = UserProfile.objects.get(user_id=user_id)
        user.userState = 'finishing_state'
        user.save()

        return TextSendMessage(text=retMessage)
    
    else:
        return TextSendMessage(text=reply["NotRaiser"])

# 顯示所有指令
def showInstruction():
    return TextSendMessage(text=reply["ShowInstruction"])

# 過濾非必要訊息   
def handleInitialState():
    return TextSendMessage(text=reply["NotInstruction"])

# 輸入會員資訊
def handleRegisteringState(user_id, message):
    user = UserProfile.objects.get(user_id=user_id)
    user_info = message.text
    item = user_info.split()
    user.userName = item[0]
    # 搜尋對應群組
    for i in range(1,len(item)):
        group, is_group_created = UserGroup.objects.get_or_create(groupName=item[i])
        user.groups.add(group)
        user.save()
        group.members.add(user)
        group.save()
        
    user.userState = 'initial_state'
    user.save()
    
    return TextSendMessage(text=reply["SuccessRegistering"])

# 輸入新訂單資訊
def handleRaisingState(user_id, message):
    user = UserProfile.objects.get(user_id=user_id)

    # Stage 1: 輸入發起的群組名稱及店名
    if isinstance(message, TextMessage): 
        message = message.text
        item = message.split()
        
        # 處理訂單上限
        orderNum = Order.objects.filter(orderState="existing").filter(orderGroupName=item[0]).count()
        if orderNum >= 3:
            user.userState = 'initial_state'
            user.save()
            
            return TextSendMessage(text=reply["ExistedOrderLimit"])
        
        # latestOrder = Order.objects.latest("createdTime")
        # newOrderID = latestOrder.orderID + 1
        
        order = Order.objects.create(orderState="existing", orderRaiserID=user_id, orderRaiserName=user.userName,
                                     orderGroupName=item[0], orderShop=item[1], orderPrice=0)

        return TextSendMessage(text=reply["InputMenu"])
    
    # Stage 2: 輸入店家菜單的圖片
    if isinstance(message, ImageMessage):
        imageContent = line_bot_api.get_message_content(message.id)

        # 將圖片儲存到server的static folder中
        imageName = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(4))
        imageName = imageName.upper()+".jpg"
        imagePath = "./static/images/" + imageName

        with open(imagePath, 'wb') as fd:
            for chunk in imageContent.iter_content():
                fd.write(chunk)
        
        order = Order.objects.filter(orderState="existing").filter(orderMenu="").get(orderRaiserID=user_id)
        order.orderMenu = "https://" + settings.ALLOWED_HOSTS[0] + imagePath[1:]
        order.save()

        print(order.orderMenu) # check

        # 訂單建立成功後，推播訂單給同群組的用戶
        group = UserGroup.objects.get(groupName=order.orderGroupName)
        members = group.members.all()
        textMessage = TextSendMessage(text="{}發起了新的訂單~~這次要訂的是「{}」，快來加入吧！".format(order.orderRaiserName, order.orderShop))
        imageMessage = ImageSendMessage(original_content_url=order.orderMenu, preview_image_url=order.orderMenu)
        textMessage2 = TextSendMessage(text="此訂單編號為 {} ，輸入「加入訂單」來選購商品吧~".format(order.id))
        
        # URL testing
        # testImageURL = "https://upload.wikimedia.org/wikipedia/commons/b/b6/Image_created_with_a_mobile_phone.png"
        # imageMessage = ImageSendMessage(original_content_url=testImageURL, preview_image_url=testImageURL)
        
        for member in members:
            line_bot_api.push_message(
                member.user_id,
                [textMessage, imageMessage, textMessage2]
            )
        
        user.userState = 'initial_state'
        user.save()

        return TextSendMessage(text=reply["SuccessRaising"])
            
    return TextSendMessage(text=reply["FailedInput"])

# 新增一筆訂購資訊在訂單中 (目前一次只能一筆進去)
def handleAddingState(user_id, message):
    user = UserProfile.objects.get(user_id=user_id)
    user.userState = 'initial_state'
    user.save()

    order_info = message.text
    item = order_info.split()

    try:
        order = Order.objects.filter(orderState="existing").get(id=item[0])
        participant = Participant.objects.create(
            user_id=user_id,  
            userName=user.userName,  
            orderName=item[1], 
            orderNum=int(item[2]), 
            price=int(item[3]) 
        )
        order.orderParticipant.add(participant)
        order.orderPrice += int(item[3])
        participant.save()
        order.save()

        return TextSendMessage(text=reply["SuccessAdding"])
    
    except Order.DoesNotExist:
        return TextSendMessage(text=reply["InvalidOrder"])

# 修改已加入的訂單內容 (目前一次只能改一筆)
def handleModifyingState(user_id, message):
    # 修改訂購資訊 (其實意思同加入訂單的操作)
    
    order_info = message.text
    item = order_info.split()

    # Stage 1: 輸入欲修改之訂單編號
    if len(item) == 1:
        order = Order.objects.get(id=item[0])
        existedContents = order.orderParticipant.filter(user_id=user_id)
        if existedContents.exists():
            content = "已選購品項：\n編號  品項  數量  價格\n"
            for existedContent in existedContents:
                content += "{}  {}  {}  {}\n".format(str(existedContent.id), existedContent.orderName, existedContent.orderNum, str(existedContent.price))
            
            content = content[:-2]   # delete \n at the end of string
            return [TextSendMessage(text=content), TextSendMessage(text=reply["InputModifyMerchandise"])]
        else:
            return TextSendMessage(text=reply["NoExistedMerchandise"])
    
    # Stage 2: 輸入欲刪除的編號
    elif len(item) == 3:
        order = Order.objects.get(id=item[0])
        chosenContent = order.orderParticipant.filter(user_id=user_id).get(id=int(item[1]))
        order.orderPrice = order.orderPrice - chosenContent.price
        chosenContent.delete()
        order.save()

    # Stage 2: 輸入欲修改的項目
    elif len(item) == 5:
        order = Order.objects.get(id=item[0])
        chosenContent = order.orderParticipant.filter(user_id=user_id).get(id=int(item[1]))
        order.orderPrice = order.orderPrice - chosenContent.price + int(item[4])
        chosenContent.orderName = item[2]
        chosenContent.orderNum = int(item[3])
        chosenContent.price = int(item[4])
        chosenContent.save()
        order.save()
        
    # 處理不合理輸入
    else:
        return TextSendMessage(text=reply["NotInstruction"])

    # 做完 stage 2 後要將用戶調整回原始狀態
    user = UserProfile.objects.get(user_id=user_id)
    user.userState = 'initial_state'
    user.save()

    return TextSendMessage(text=reply["SuccessModifying"])

# 結束已發起的某一訂單
def handleFinishingState(user_id, message):
    orderList = Order.objects.filter(orderState="existing").filter(orderRaiserID=user_id)
    user = UserProfile.objects.get(user_id=user_id)
    user.userState = 'initial_state'
    user.save()
    
    try:
        targetOrder = orderList.get(id=int(message.text))
        targetOrder.orderState = "finished"
        targetOrder.save()
        # 顯示所有訂單資訊給同群組的用戶
        group = UserGroup.objects.get(groupName=targetOrder.orderGroupName)
        members = group.members.all()
        textMessage1 = TextSendMessage(text="{}發起的訂單已結單，以下將顯示所有訂單資訊，感謝您的使用。".format(targetOrder.orderRaiserName))
        textMessage2 = TextSendMessage(text=targetOrder.__str__())
        for member in members:
            line_bot_api.push_message(
                member.user_id,
                [textMessage1, textMessage2]
            )
           
        return [TextSendMessage(text=reply["SuccessFinishing"]), TextSendMessage(text=targetOrder.__str__())]
        
    except Order.DoesNotExist: 
        return TextSendMessage(text=reply["FailedInput"])


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
 
        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
 
        for event in events:
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                user_id = event.source.user_id
                
                if isinstance(event.message, TextMessage):
                    textInput = event.message.text
                else:
                    textInput = "NotText"
                
                # 管理用戶狀態 ["initial_state", "registering_state", "raising_state", "adding_state", "modifying_state", "finishing_state"]
                # 優先處理會員註冊
                isRegisteredUser = UserProfile.objects.filter(user_id=user_id).exists()
                if not isRegisteredUser and not textInput == "註冊會員":
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply["NotMember"])
                    )
                    continue
                
                if isRegisteredUser:
                    user = UserProfile.objects.get(user_id=user_id)
                    user_state = user.userState


                # 指定動作處理
                # 會員註冊
                if textInput == "註冊會員":
                    content = registerMember(user_id, isRegisteredUser)
                
                # 發起訂單
                elif textInput == "發起訂單":
                    content = raiseOrder(user_id)
                
                # 加入訂單
                elif textInput == "加入訂單":
                    content = addOrder(user_id)
                
                # 修改訂單
                elif textInput == "修改訂單":
                    content = modifyOrder(user_id)
                
                # 顯示訂單內容
                elif textInput == "訂單內容":
                    content = showOrderStatus(user_id)
                
                # 結單
                elif textInput == "訂單總結":
                    content = finishOrder(user_id)
                
                # 查詢指令
                elif textInput == "指令查詢":
                    content = showInstruction()

                # 非指定動作之訊息處理
                else:
                    if user_state == "initial_state":
                        content = handleInitialState()
                    elif user_state == "registering_state":
                        content = handleRegisteringState(user_id, event.message)
                        
                    elif user_state == "raising_state":
                        content = handleRaisingState(user_id, event.message)
                            
                    elif user_state == "adding_state":
                        content = handleAddingState(user_id, event.message)
                        
                    elif user_state == "modifying_state":
                        content = handleModifyingState(user_id, event.message)

                    elif user_state == "finishing_state":
                        content = handleFinishingState(user_id, event.message)

                line_bot_api.reply_message(event.reply_token, content)
                    
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

