from django.db import models

# Create your models here.

class Order(models.Model):
    orderState = models.CharField(max_length=20, default="existing")           # ["finished", "existing"]
    # orderID = models.IntegerField(default=0)                                   # order ID (0317 modified)
    orderRaiserID = models.CharField(max_length=50, default="NoRaiserID")      # raiser's user id
    orderRaiserName = models.CharField(max_length=50, default="NoRaiserName")  # raiser's user name
    orderGroupName = models.CharField(max_length=100, default="NoGroupName")   # raiser's belonging group
    orderShop = models.CharField(max_length=100, default="NoShopName")         # shop name
    orderMenu = models.CharField(max_length=255, default="", blank=True)       # shop menu (URL form)
    orderPrice = models.IntegerField(default=0)                                # order's total price
    lastModifiedTime = models.DateTimeField(auto_now=True)
    createdTime = models.DateTimeField(auto_now_add=True)
    orderParticipant = models.ManyToManyField("Participant")                   # all participants' order
    
    def __str__(self):
        stringFront = f"訂單編號：{self.id}\n訂單發起者：{self.orderRaiserName}\n店家名稱：{self.orderShop}\n當前訂單內容：\n\n    訂購人  品項  數量  價格\n"
        # 把所有訂購餐點都list出來
        participants_info = ""
        for participant in self.orderParticipant.all():
            participants_info += str(participant) + "\n"
        
        stringBack = "\n當前訂單總價：{}\n最後修改時間：{}".format(str(self.orderPrice), str(self.lastModifiedTime))
        return stringFront + participants_info + stringBack
    
    class Meta:
        db_table = "tb_order"
    
class Participant(models.Model):
    user_id = models.CharField(max_length=50, default="NoParticipantID")       # participant's user id
    userName = models.CharField(max_length=100, default="NoParticipantName")   # username
    orderName = models.CharField(max_length=100, default="NoOrderName")        # participant's order
    orderNum = models.IntegerField(default=1)                                  # number of participant's order
    price = models.IntegerField(default=0)                                     # price of participant's order
    
    def __str__(self):
        return f"    {self.userName}  {self.orderName}  {self.orderNum}  {self.price}"
    
    class Meta:
        db_table = "tb_participant"
        
class UserProfile(models.Model):
    user_id = models.CharField(max_length=50, default="NoUserID")              # user_id
    userState = models.CharField(max_length=100, default="initial_state")      # user state
    userName = models.CharField(max_length=100, default="NoUserName")          # user name
    groups = models.ManyToManyField('UserGroup', related_name='user_groups')   # group user in
    # email = models.EmailField(max_length=100, blank=True, null=True)  
    # phone_number = models.CharField(max_length=20, blank=True, null=True)  

    def __str__(self):
        return self.userName

    class Meta:
        db_table = "user_profile"
        
class UserGroup(models.Model):
    groupName = models.CharField(max_length=100, default="NoGroupName")        # group name
    members = models.ManyToManyField('UserProfile', related_name='group_members')     # all members in group 

    def __str__(self):
        return self.groupName

    class Meta:
        db_table = "user_group"