from flask import Flask,render_template         # flask web server
from irControl import control                   # keyName decode위한 함수 import
from time import sleep                          # servo motor 움직임 시간
from flask_socketio import SocketIO, emit       # Websocket 사용
import Adafruit_DHT                             # 온습도 센서 DHT11 사용 위함
import datetime                                 # 현재 날짜 및 시간 표시
import RPi.GPIO as GPIO                   

humSensor = Adafruit_DHT.DHT11                  # Adafruit library 사용
humSensorPin = 2 	#BCM, phy = 3               library에서 BCM 사용

#핀 번호 선언, physical number
LED_PIN = 26 		
irReceiver = 12		
IR_PIN = 11		
SERVO_PIN= 32 		

hum, tem = Adafruit_DHT.read_retry(humSensor, humSensorPin)	#read data and store
app = Flask(__name__)                                       #app 객체 생성
socketio = SocketIO(app)                                    #SocketIO 객체 생성

#핀 모드 설정 및 초기화
GPIO.setmode(GPIO.BOARD)                                    #physical num으로 지정한 이유
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)             #LED OFF init
GPIO.setup(SERVO_PIN, GPIO.OUT)                             #SERVO PIN init
#GPIO.setup(irReceiver, GPIO.IN)                            #에어컨 리모컨 신호 받을 때, 사용X
GPIO.setup(IR_PIN, GPIO.OUT)                                #IR Trasmitter

#setting servo motor pin and duty rate
servo = GPIO.PWM(SERVO_PIN, 50)                             #PWM mode, 50Hz
servo.start(0)                                              #start servo, if duty=0, not run
servo_max_duty = 12                                         #max, min duty rate 설정
servo_min_duty = 3

#실행 시 첫 화면
@app.route('/')
def home():
    return render_template('home.html')

# WebSocket 연결 시 10초마다 데이터 전송
@socketio.on('connect')
def handle_connect():
    while True:
        hum, tem = Adafruit_DHT.read_retry(humSensor, humSensorPin)
        if hum is not None and tem is not None:
            badFeel = (1.8 * tem - 0.55 * (1 - hum) * (1.8 * tem - 26) + 32) / 10.0
            feel = "TERRIBLE!!" if badFeel > 80 else "BAD" if badFeel > 75 else "NOT GOOD" if badFeel >= 68 else "GOOD:)"
            sensorData = {
                'hum': hum,
                'tem': tem,
                'feelIndex': int(badFeel),
                'feel': feel
            }
            emit('sensor_data', sensorData)  # 클라이언트로 실시간 데이터 전송
        sleep(10)

#main page
@app.route('/inform')
def inform():
    now = datetime.datetime.now()                           #시간
    timeString = now.strftime("%Y-%m-%d %H:%M")             #년-월-일 시간-분
    badFeel=(1.8*tem - 0.55*(1-hum)*(1.8*tem-26) + 32)/10.0 #불쾌지수 = 시카고 대학 기후학자 Tomn 제안
    feelString=str(int(badFeel))                            #문자로 변환
    
    # 불쾌지수에 따른 기분 4단계 - Tomn
    if badFeel>=68 and badFeel<=75 :
        feel='NOT GOOD'
    elif badFeel>75 and badFeel<=80:
        feel='BAD'
    elif badFeel>80:
        feel='TERRIBLE!!'
    else:
        feel='GOOD:)'
        
    # web page에 전달할 sensorData Dictionary
    sensorData = {
        'hum' : hum,                  #습도
        'tem': tem,                   #온도
        'feelIndex':feelString,       #불쾌 지수
        'feel': feel,                 #기분
        'time' : timeString           #측정 시간
    }
    
    #DHT sensor가 정상 동작 할 때 실행, 그렇지 않으면 error
    if hum is not None and tem is not None:
        return render_template('inform.html', **sensorData)
    else:
        return "<h1> Failed to get reading!!!! </h1>"
    
#air conditioner ON   
@app.route('/aircon/on')
def aircon_on():
    try:
            GPIO.output(LED_PIN, GPIO.HIGH)             #LED ON
            control('POWER_ON')                         #irsend decode - air conditioner on
            return render_template('inform.html')       #show webpage
    except KeyboardInterrupt:                           #end
        pass
    GPIO.cleanup()                                     
        
#air conditioner OFF
@app.route('/aircon/off')
def aircon_off():
    try:
            GPIO.output(LED_PIN, GPIO.LOW)              #LED OFF
            control('POWER_OFF')                        #irsend decode - air conditioner off
            return render_template('inform.html')       #show webpage
    except KeyboardInterrupt:
        pass
    GPIO.cleanup()
    

#servo motor : PWM 사용 = analog->digital
#문제점 : 떨림이 심해서 다양한 방법을 찾아보았지만 완전히 없애기는 어려운 듯 하다.
#duty비를 우리가 사용하는 각도로 전환하는 함수
def set_servo_degree(degree):
    if degree > 180:
            degree = 180	    #max=180
    elif degree < 0:
            degree = 0	        #min=0
        
    #duty 계산은 다른 코드 참고, 180도를 기준으로 하는 것 같다.
    duty = servo_min_duty + (degree*(servo_max_duty-servo_min_duty)/180.0)

    GPIO.setup(SERVO_PIN, GPIO.OUT)     #servomotor pin out mode
    servo.ChangeDutyCycle(duty)         #각도 조절
    sleep(0.7)                          #다음 동작까지 시간 주기
    #GPIO.setup(SERVO_PIN, GPIO.IN)	    #not ddulim 떨림이 너무 심해서 시도해보았던 것, 효과가 미미하다.
    
#window OPEN
@app.route('/window/open')
def window_open():
    try:
        set_servo_degree(70)                        #window open
        return render_template('inform.html')       #show webpage
        sleep(1.3)                                  #motor 움직일 시간
    except KeyboardInterrupt:
        GPIO.cleanup(SERVO_PIN)
        pass
    
#window CLOSE
@app.route('/window/close')     
def window_close():
    try:
        set_servo_degree(180)                       #window open
        return render_template('inform.html')       #show webpage
        sleep(1.3)
    except KeyboardInterrupt:
        GPIO.cleanup(SERVO_PIN)
        pass

#Websocket으로 수정
if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", post=8080)
    
GPIO.cleanup()               #프로그램 종료 시 파이썬 프로그램 내 초기화 했던 핀 설정 초기화
        
