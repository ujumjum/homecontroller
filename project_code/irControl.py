#IR sensor 연결 확인 sudo /etc/init.d/lircd status

#remote.py -> cmd로 명령어 전달 위한 함수
from os import system as cmd

# 1. remote.py에서 전달된 keyName data
def control(keyName):
    #3. cmd창에 명령어 입력해서 적외선 송신
    #sudo /etc/init.d/lircd status로 이름 알 수 있음
    cmd("irsend SEND_ONCE LGE_6711A20015N " + __decode(keyName))    
    
# 2. 에어컨 정보가 담긴 6711A20015N.lircd.conf 
def __decode(keyName):
    POWER_ON="UN-JEON/JEONG-JI_18"      #POWER ON setting 18 degree, 다양한 코드가 있는데 이거 사용
    
    POWER_OFF="UN-JEON/JEONG-JI_OFF"    #"0xC0051" #UN-JEON/JEONG-JI_OFF
    
    print("air conditioner " + keyName) #debug code
    
    return eval(keyName)                #값 전달
