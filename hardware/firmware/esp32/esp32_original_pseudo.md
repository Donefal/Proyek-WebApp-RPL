func alert(pin):
	tone up the buzzer for t second

func recieveFromAPI():
	IF WiFi IS connected:
		establish HTTP connection with the API
	begin GET from API:
		GET responseCode
		CASE:
			IF (responseCode == 200): //success
				CREATE response: string
				response = CALL HTTP.getString()
	RETURN response

func sendToAPI(data):
		IF WiFi IS connected:
		establish HTTP connection with the API
	begin POST to API:
		CREATE stringPayload
		pack data to stringPayload
		
		CALL HTTP.POST(stringPayload)
	GET responseCode:
		PRINT to serial the reponseCode

func testAPI():
	IF Wifi IS connected:
		establish HTTP connection with the API
	begin POST to API:
		PRINT to serial the responseCode
	begin GET to API:
		PRINT to serial the responseCode

func SETUP():
	Start serial
	Setup pin modes FOR EACH sensor
		Trig pins (OUTPUT)
		Echo pins (INPUT)
	Setup pin modes FOR EACH servo
		Must be a PWM pins
	Connect to WiFi
	CALL testAPI()

func LOOP():
	FOR each slot:
		CREATE occupied

	Measure the distance
		On slot:1
		On slot:2
		On slot:3
	CASE: 
		IF (distance < 10):
			occupied = true
		ELSE:
			occupied = false
	Pack into an ARRAY or VECTOR
	
	CALL recieveFromAPI()
		recieved data: slot condition
		CREATE slotCondition
			no: int
			booked: bool
			confirmed: bool
			calculated: bool
			+ occupied: bool
		CREATE gateCondition
			enterShouldOpen: bool
			exitShouldOpen: bool
	
	>>> Sistem peringatan 
	FOR EACH slot:
		CASE:
			IF (slot IS NOT calculated):
				CASE:
					IF (slot IS occupied AND NOT confirmed):
						CALL alert(slot number) >> ASYNC
					IF (slot IS occupied AND NOT booked):
						CALL alert(slot number) >> ASYNC
					IF (slot IS occupied AND booked AND confirmed):
						begin calculation for that slot
						calculated = TRUE
	
	>>> Sending data to API
	CREATE dataToSend
		FOR EACH slot
			no: int
			occupied: bool
			calculated: bool
            enterShouldOpen: bool
            exitShouldOpen: bool
	FOR EACH calculated slot:
		CASE:
			IF (slot IS NOT occupied):
				MEANS the driver is going away
	
	>>> Gerbang
	CASE:
		IF (enterShouldOpen):
			Open Enter Gate for t second
			Close Enter Gate
		IF(exitShouldOpen):
			Open Exit Gate for t second
			Close Enter Gate

	CALL sendToAPI(dataToSend)