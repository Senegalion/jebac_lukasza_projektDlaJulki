
char controllerInput = 0;  

void setup() {
  // Ustawienie pinów jako wyjścia
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
 Serial.begin(19200);
  // Konfiguracja timera 1 dla PWM na pinach 9 (OC1A) i 10 (OC1B)
  TCCR1A = _BV(COM1A0) | _BV(COM1B0); // Włącz tryb Toggle dla OC1A i OC1B
  TCCR1B = _BV(WGM12) | _BV(CS11);   // Tryb CTC (Clear Timer on Compare Match) + prescaler 8
  setPWMFrequency(600); // Ustawienie częstotliwości na 1 kHz

  pinMode(8, OUTPUT);
  pinMode(7, OUTPUT);
 // digitalWrite(8, LOW);                   // Ustaw pin 9 na stały LOW
  //digitalWrite(7, LOW); 

          TCCR1A &= ~(_BV(COM1A0) | _BV(COM1B0)); // Wyłącz sterowanie pinami 9 i 10 przez timer
  TCCR1B &= ~_BV(CS11);                   // Wyłącz zegar timera
  digitalWrite(9, LOW);                   // Ustaw pin 9 na stały LOW
  digitalWrite(10, LOW);  
}

void loop() {


   if (Serial.available() > 0) {
    // read the incoming byte:
    controllerInput=Serial.read();}

    switch (controllerInput){
  case ('s'):
    TCCR1A |= _BV(COM1A0) | _BV(COM1B0); // Załącz tryb Toggle na OC1A i OC1B
    TCCR1B |= _BV(CS11);  
    digitalWrite(8, LOW);                   // Ustaw pin 9 na stały LOW
    digitalWrite(7, HIGH);  
    break;
  case ('w'):
    digitalWrite(8, HIGH);                   // Ustaw pin 9 na stały LOW
    digitalWrite(7, LOW); 
    TCCR1A |= _BV(COM1A0) | _BV(COM1B0); // Załącz tryb Toggle na OC1A i OC1B
    TCCR1B |= _BV(CS11);                 // Włącz timer (prescaler 8)
    break;
  case ('e'):
    digitalWrite(8, LOW);                   // Ustaw pin 9 na stały LOW
    digitalWrite(7, LOW); 
      TCCR1A |= _BV(COM1A0) | _BV(COM1B0); // Załącz tryb Toggle na OC1A i OC1B
    TCCR1B |= _BV(CS11);                 // Włącz timer (prescaler 8)
delay(3500);
        TCCR1A &= ~(_BV(COM1A0) | _BV(COM1B0)); // Wyłącz sterowanie pinami 9 i 10 przez timer
  TCCR1B &= ~_BV(CS11);                   // Wyłącz zegar timera
  digitalWrite(9, LOW);                   // Ustaw pin 9 na stały LOW
  digitalWrite(10, LOW);
  controllerInput = 'x'; 
      break;
  case ('q'):
      digitalWrite(8, HIGH);                   // Ustaw pin 9 na stały LOW
    digitalWrite(7, HIGH); 
        TCCR1A |= _BV(COM1A0) | _BV(COM1B0); // Załącz tryb Toggle na OC1A i OC1B
  TCCR1B |= _BV(CS11); 
  delay(3500);
        TCCR1A &= ~(_BV(COM1A0) | _BV(COM1B0)); // Wyłącz sterowanie pinami 9 i 10 przez timer
  TCCR1B &= ~_BV(CS11);                   // Wyłącz zegar timera
  digitalWrite(9, LOW);                   // Ustaw pin 9 na stały LOW
  digitalWrite(10, LOW);                 // Włącz timer (prescaler 8)
  controllerInput = 'x';
      break;
  case ('x'):  
        TCCR1A &= ~(_BV(COM1A0) | _BV(COM1B0)); // Wyłącz sterowanie pinami 9 i 10 przez timer
  TCCR1B &= ~_BV(CS11);                   // Wyłącz zegar timera
  digitalWrite(9, LOW);                   // Ustaw pin 9 na stały LOW
  digitalWrite(10, LOW);  
      break;






}
}

void setPWMFrequency(int frequency) {
  // Oblicz wartość OCR1A na podstawie wzoru: OCR1A = (16e6 / (prescaler * frequency)) - 1
  int prescaler = 8; // Domyślnie ustawiony prescaler to 8 (CS11)
  int ocrValue = (16000000 / (prescaler * frequency)) - 1;

  // Ustaw OCR1A
  OCR1A = ocrValue;
}
