#importeren van module die nodig is voor het uitlezen van de Arduino via usb
from xmlrpc.client import boolean

import serial
#importeren van module die nodig is voor het connecteren en bewerken van de sqlite db
import sqlite3
import time
import re

#initialiseren van de poorten die nodig zijn om de arduino via usb uit te lezen
SERIAL_PORT = '/dev/cu.usbmodem11301' #deze is specifiek voor macOS, voor windows dient deze waarde COM3 te zijn
BAUD_RATE = 115200
DATABASE_FILE = 'saturatie_data.db' #aanroepen correcte sqlite db

#aanmaken methode aanroepen db
def create_database_connection(db_file):
    conn = None #zet default op None
    try: #proberen of de connectie opgebouwd kan worden dmv. het aangeleverde bestand in de method aanroep)
        conn = sqlite3.connect(db_file)
        print(f"Succesvol verbonden met database {db_file}") #als succesvol connectie dan weergeven dat het gelukt is
    except sqlite3.Error as e: #indien de connectie opbouw niet gelukt is, dan error message printen
        print(e)
    return conn #geeft connection string terug; dit is connectie naar sqlite of indien mislukt nog steeds None

#invoegen van data in database methode
def insert_data(conn, data):
    #SQL query
    sql = ''' INSERT INTO metingen(hartslag, spo2) VALUES (?, ?) ''' #SQL query string die schrijft de waarden (nog onbekend) naar de kolommen hartslag en spo2 in de sqlite
    try:
        cur = conn.cursor() #initialiseren cursor voor het kunnen lezen/schrijven van de data
        cur.execute(sql, data) #uitvoeren van SQL query met de data die beschikbaar via de methode
        conn.commit() #vastleggen/opslaan in database
        return cur.lastrowid #teruggeven van de laatste rij
    except sqlite3.Error as e: #indien error
        print(f"Database error: {e}") #weergeven gegenereerde error code
        return None #teruggeven van 'None'


def main():
    db_conn = create_database_connection(DATABASE_FILE) #creeren van db connectie string
    if db_conn is None: #indien db_conn leeg is dan..
        print("Kan geen databaseverbinding maken. Script stopt.") #aangeven dat er geen connectie gemaakt kan worden
        return

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) #maak verbinding met de seriële poort
        print(f"Luisteren naar seriële poort {SERIAL_PORT} op {BAUD_RATE} baud...") #weergeven op welke poort en snelheid geluisterd wordt
        time.sleep(2)  #geef de verbinding even de tijd om te stabiliseren

        while True:
            if ser.in_waiting > 0: #wacht op data van de Arduino
                line = ser.readline().decode('utf-8').strip() #decode data naar utf-8 codeset en verwijderd overbodige whitespaces
                #data_values = [] #lijst initialiseren en leeg maken voor nieuw gebruik
                #if line in line: #controleer of de lijn data bevat en het juiste format heeft
                #hartslag = 0
                hartslag = round(float(line))
                spo2 = 100.0
                meting_id = insert_data(db_conn, (hartslag, spo2))  # voeg de data toe aan de database via methode met de correcte  variabelen die nodig zijn
                if meting_id:
                    print(f"Data ontvangen en opgeslagen (ID: {meting_id}): Pulse={hartslag}")  # teruggeven indien gelukt met db ID, hartslag waarde en spo2 waarde
                else:
                    print('Invalid data received')
                    '''try:
                        print(line)
                        hartslag = int(line)
                        print(hartslag)
                        #red_ledcolor, ir_ledcolor, hartslag, valid_hr, spo2, valid_spo2 = line.split(',') #lijn uitsplitsen in alle nieuwe variabelen nl. hartslag en spo2
                        #data_values = line.split(',') #opslaan data waarden in lijst
                        #hartslag = int(hartslag) omzetten string naar int -- eruit halen, hartslag heeft foutieve conversie in huidige arduino code
                        #for item in data_values:
                            #if ("SPO2Valid=1" == item): #controle of geldige spo2 meting (hoort 1 te zijn)
                                #if ("SPO2=" in item): #correcte veld ophalen spo2
                                 #   getal_uit_string = int(item.split("=")[1].strip()) #string splitsen alleen laatste gedeelte nummer nodig, eventueel whitespace weg en omzetten naar int
                        meting_id = insert_data(db_conn, hartslag)  # voeg de data toe aan de database via methode met de correcte  variabelen die nodig zijn
                        if meting_id:
                            print(
                                f"Data ontvangen en opgeslagen (ID: {meting_id}): Pulse={hartslag}")  # teruggeven indien gelukt met db ID, hartslag waarde en spo2 waarde
                        else:
                            print('Invalid data received')

                    except ValueError:
                        print(f"Ongeldige data ontvangen: '{line}' - wordt overgeslagen.") #indien geen geldige data aangeven dat deze wordt overgeslagen
                    except Exception as e:
                        print(f"Een onverwachte fout is opgetreden: {e}") #indien error, dan betreffende error weergeven aan gebruiker
                    '''
    except serial.SerialException as e:
        print(f"Fout met de seriële poort: {e}") #indien error, gebruiker informeren
        print(f"Controleer of de poort '{SERIAL_PORT}' correct is en niet in gebruik door een andere applicatie (zoals de Arduino Seriële Monitor).") #gebruiker informeren om de correct poort settings te verifieren
    except KeyboardInterrupt:
        print("\nScript gestopt door gebruiker.") #indien interrupt door eindgebruiker, dit melden in console
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close() #sluiten seriele verbinding
            print("Seriële poort gesloten.") #terugkoppelen gebruiker gesloten seriele verbinding
        if db_conn:
            db_conn.close() #sluiten database connectie
            print("Databaseverbinding gesloten.") #terugkoppelen gebruiker dat db connectie is gesloten



if __name__ == '__main__':
    main() #aanroep hoofd programma en uitvoering starten


