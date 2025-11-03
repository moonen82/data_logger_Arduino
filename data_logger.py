#importeren van module die nodig is voor het uitlezen van de Arduino via usb
import serial #importeren van module die nodig is voor het connecteren en bewerken van de sqlite db
import sqlite3
import time
import dash
from dash import dcc, html # nodig voor opbouw pagina met html
from dash.dependencies import Input, Output # mogelijk nodig voor dropdown ed. in grafieken
import pandas as pd
import plotly.express as px


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

def read_data(conn):
    read_query = '''SELECT hartslag, spo2 FROM metingen'''  # query opstellen voor uitlezen hartslag en spo2 data uit sqlite db
    data_frame = pd.read_sql(read_query, conn) # via pandas query uitvoeren op db en connectie maken met db
    return data_frame


#def main():
db_conn = create_database_connection(DATABASE_FILE) #creeren van db connectie string
if db_conn is None: #indien db_conn leeg is dan..
    print("Kan geen databaseverbinding maken. Script stopt.") #aangeven dat er geen connectie gemaakt kan worden


main_data_frame = read_data(db_conn) # ophalen data uit sqlite en in dataframe beschikbaar maken
graph_type_options = [
    {'label': 'Hartslag', 'value': 'hartslag'},
    {'label': 'Saturatie', 'value': 'spo2'},
]

# print(main_data_frame) # test regel om te kijken hoe de data eruit komt -- tzt verwijderen

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

app = dash.Dash(__name__)
# server = app.server

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children= [

    html.H1(
        "Hartslag en Saturatie metingen",
        style={'textAlign': 'center'}
    ),
    html.Div(
        [
            html.Label(
                "Filter metingen",
                style={'fontWeight': 'bold', 'marginRight': '10px'}
            ),

            dcc.Dropdown(
                id='meting-dropdown',
                options=graph_type_options,
                value='hartslag',
                clearable=False,
                style={'width': '50%', 'minWidth': '200px', 'display': 'inline-block'}
            ),
        ],
        style={'marginBottom': '20px', 'padding': '15px', 'border': '1px solid black', 'borderRadius': '5px'}
    ),
    html.Div(
        [
            dcc.Graph(id='meting-graph')
        ]
    )
])

@app.callback(
    Output('meting-graph', 'figure'),
    [Input('meting-dropdown', 'value')]
)
def update_meting(selected_graph_type):
    if selected_graph_type == 'hartslag':
        grouped_data_frame = main_data_frame.groupby('hartslag')
        title = "Hartslag"
        fig = px.histogram(grouped_data_frame, x='hartslag')

    fig.update_layout(
        transition_duration=500
    )

    return fig


if __name__ == '__main__':
    print("Dash app is running...")
    print(f"Open your browser at http://127.0.0.1:8050/")
    app.run(debug=True)


