---------------------------------------------
FUNCTION alert(slotPin):
    play buzzer tone for T seconds
---------------------------------------------

FUNCTION getFromAPI():
    IF WiFi connected:
        http.begin(GET_URL)
        responseCode = http.GET()

        IF responseCode == 200:
            response = http.getString()
            parsedData = parse JSON (slotCondition + gateCondition)
            RETURN parsedData
        ELSE:
            RETURN null
    ELSE:
        reconnect WiFi
---------------------------------------------

FUNCTION sendToAPI(data):
    IF WiFi connected:
        http.begin(POST_URL)
        http.addHeader("Content-Type", "application/json")

        payload = convert data to JSON
        responseCode = http.POST(payload)

        print responseCode
---------------------------------------------

FUNCTION testAPI():
    IF WiFi connected:
        test GET
        print results
        test POST
        print results
---------------------------------------------

FUNCTION setup():
    start Serial
    setup trig/echo pins
    setup servo pins (PWM)
    connect WiFi
    call testAPI()
---------------------------------------------

FUNCTION readSlotSensors():
    FOR each slot:
        measure distance using ultrasonic
        IF distance < THRESHOLD:
            occupied = true
        ELSE:
            occupied = false
    
    RETURN array of occupied values
---------------------------------------------

FUNCTION processSlotLogic(slotStates, apiSlotData):
    FOR each slot:
        IF NOT apiSlotData[slot].calculated:
            
            IF slotStates[slot] == occupied AND NOT confirmed:
                alert(slot)

            IF slotStates[slot] == occupied AND NOT booked:
                alert(slot)

            IF slotStates[slot] == occupied AND booked AND confirmed:
                mark as calculated

    RETURN updated slotStates
---------------------------------------------

FUNCTION controlGates(gateCondition):
    IF gateCondition.enterShouldOpen:
        open enter servo for T seconds
        close servo

    IF gateCondition.exitShouldOpen:
        open exit servo for T seconds
        close servo
---------------------------------------------

FUNCTION loop():
    slotStates = readSlotSensors()

    apiData = getFromAPI()
    IF apiData IS NOT null:
        slotStates = processSlotLogic(slotStates, apiData.slotCondition)
        controlGates(apiData.gateCondition)

    dataToSend = package slotStates + calculated states
    sendToAPI(dataToSend)

    delay(2000)   // avoid spamming server
