import urllib.parse
import pandas as pd
import requests
import datetime
import streamlit as st
import time

# Function to handle rate limiting
requests_made = 0
last_minute = time.time()
last_30min = time.time()

def rate_limit_check():
    global requests_made, last_minute, last_30min
    
    current_time = time.time()
    
    # Check per second limit
    if current_time - last_minute < 1:
        if requests_made >= 25:
            time.sleep(1 - (current_time - last_minute))
        requests_made = 0
        last_minute = current_time
    
    # Check per minute limit
    if current_time - last_minute < 60:
        if requests_made >= 250:
            time.sleep(60 - (current_time - last_minute))
        requests_made = 0
        last_minute = current_time
    
    # Check per 30 minutes limit
    if current_time - last_30min < 1800:
        if requests_made >= 1000:
            time.sleep(1800 - (current_time - last_30min))
        requests_made = 0
        last_30min = current_time

    requests_made += 1

# API Credentials
apiKey = 
secretKey = 
redirect_uri = #Create Upstox 

# Encode the redirect URI
encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe="")

# Streamlit UI
st.set_page_config(layout="wide")

# To Generate Request
def make_request(method, url, headers=None, params=None, data=None):
    rate_limit_check()  # Check and wait if rate limit exceeded
    
    response = None
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, params=params, json=data)
        else:
            raise ValueError('Invalid HTTP method.')
        
        if response.status_code == 200:
            return response.json()
        else:
            return response
    except requests.exceptions.RequestException as e:
        print(f'An error occurred: {e}')
        return None
    

indices_lst = ["NIFTY BANK", "NIFTY AUTO", "NIFTY FINANCIAL SERVICES", "NIFTY FINANCIAL SERVICES 25 50", 
               "NIFTY FMCG", "NIFTY IT", "NIFTY MEDIA", "NIFTY METAL", "NIFTY PHARMA", "NIFTY PSU BANK", 
               "NIFTY PRIVATE BANK", "NIFTY REALTY", "NIFTY HEALTHCARE", "NIFTY CONSUMER DURABLES", 
               "NIFTY OIL & GAS", "NIFTY MIDSMALL HEALTHCARE"]
stock_detail_df = pd.read_csv("instrument_key.csv")

def data_filter(df, stock_detail_df):
    filtered_df = stock_detail_df[stock_detail_df['tradingsymbol'].isin(df['SYMBOL \n'])]
    filtered_df.reset_index(inplace = True)
    filtered_df.drop(columns=['index', 'expiry', 'strike', 'tick_size', 'lot_size', 'instrument_type', 'option_type', 'exchange', 'exchange_token'], inplace=True)
    filtered_df = filtered_df.sort_values(by='last_price')
    return filtered_df

# 
def finder(filtered_df):
    opportunities_list = []
    total_opportunities = 0
    all_opportunities_data = []

    for i in range(filtered_df.shape[0]):
        try:
            # Construct the URL for fetching candle data
            url = f'https://api.upstox.com/v2/historical-candle/intraday/{filtered_df["instrument_key"][i]}/1minute'
            headers = {'Accept': 'application/json'}

            # Fetch the candle data
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            candles_data = response.json().get('data', {}).get('candles', [])

            if candles_data:
                # Create a DataFrame from the candle data
                df = pd.DataFrame(candles_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
                df.drop(columns=['OI'], inplace=True)
                df['Price Range %'] = ((df['High'] - df['Low']) / df['Low']) * 100

                # Filter for opportunities where Price Range % is greater than or equal to 0.5%
                filtered_df_opp = df[df['Price Range %'] >= 0.5].copy()

                if not filtered_df_opp.empty:
                    # Process the filtered opportunities
                    filtered_df_opp['Timestamp'] = pd.to_datetime(filtered_df_opp['Timestamp'])
                    filtered_df_opp.sort_values(by='Timestamp', ascending=False, inplace=True)
                    latest_opportunity = filtered_df_opp.iloc[0]  # Take only the latest opportunity

                    # Check if the LOW price is less than or equal to 300
                    if latest_opportunity['Low'] <= 300:
                        # Update total opportunities count
                        total_opportunities += 1

                        # Prepare data for DataFrame
                        symbol = filtered_df["tradingsymbol"][i]
                        avg_price_range = latest_opportunity['Price Range %']
                        latest_opportunity_time = latest_opportunity['Timestamp'].strftime('%I:%M %p')  # Format time in 12-hour format
                        open_price = latest_opportunity['Open']
                        high_price = latest_opportunity['High']
                        low_price = latest_opportunity['Low']
                        close_price = latest_opportunity['Close']

                        all_opportunities_data.append({
                            'Symbol': symbol,
                            'Average Price Range %': avg_price_range,
                            'Latest Opportunity': latest_opportunity_time,
                            'Total Opportunities': total_opportunities,
                            'Open': open_price,
                            'High': high_price,
                            'Low': low_price,
                            'Close': close_price
                        })

        except requests.exceptions.HTTPError as err:
            print(f"Error fetching data for {filtered_df['tradingsymbol'][i]}: {err}")

    # Create DataFrame from collected data
    opportunities_df = pd.DataFrame(all_opportunities_data)

    # Sort opportunities_df by 'Latest Opportunity' in descending order
    opportunities_df.sort_values(by='Latest Opportunity', ascending=False, inplace=True)

    col1, col3, col4, col5, col6, col7, col8 = st.columns(7)

    for index, row in opportunities_df.iterrows():
        with col1:
            st.code(row['Symbol'])

        with col3:
            st.code(row['Latest Opportunity'])  # Display only the time in 12-hour format

        with col4:
            st.code(f"{row['Total Opportunities']}")

        with col5:
            st.code(f"{row['Open']}  Open")

        with col6:
            st.code(f"{row['High']}  High")

        with col7:
            st.code(f"{row['Low']}  Low")

        with col8:
            st.code(f"{row['Close']}  Close")
# Streamlit UI
st.title("Opportunities for 1 Min Tick Size")

# Generate the authorization link
st.markdown("---")
st.markdown("*Click The Below Link & Enter Your Credentials*")
upstox_link = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={apiKey}&redirect_uri={encoded_redirect_uri}"
st.markdown(f"[Login with Upstox]({upstox_link})")
st.markdown("---")

# Start button to begin finding opportunities
if st.button("Start Finder Using Indices", key="indices_finder"):
    for i in indices_lst:
        j = f"data\\{i.replace(' ', '-')}.csv"
        df = pd.read_csv(j)
        df = df[1:]
        st.write(f"*{i}*")
        filtered_df = data_filter(df, stock_detail_df)
        finder(filtered_df)

if st.button("Start Finder Using NIFTY 500", key="nifty500_finder"):
    df = pd.read_csv("NIFTY-500.csv")
    df = df[1:]
    st.write(f"*NIFTY 500*")
    filtered_df = data_filter(df, stock_detail_df)
    finder(filtered_df)

if st.button("Start Finder Using All Companies", key = "allcompanies_finder"):
    seg =["MEDICO", "TRIDENT", "CENTRUM", "PFS", "UDAICEMENT", "UNIINFO", "VIPULLTD", "BGRENERGY", "GOKUL", "FIBERWEB", "SHIVAMAUTO", "GENCON", "KOHINOOR", "BAJAJHIND", "MTNL", "EASEMYTRIP", "DHANBANK", "TREL", "PTL", "ARENTERP", "TCLCONS", "INDORAMA", "MADHAV", "BASML", "TV18BRDCST", "NDL", "JETAIRWAYS", "MIRZAINT", "KCPSUGIND", "LANCORHOL", "KMSUGAR", "OSWALAGRO", "INCREDIBLE", "AGROPHOS", "NIRAJ", "MURUDCERA", "BANG", "ESSARSHPNG", "NGIL", "JAIPURKURT", "PIONEEREMB", "GUJRAFFIA", "AAREYDRUGS", "JAYNECOIND", "DHANI", "DBSTOCKBRO", "ANIKINDS", "CORALFINAC", "HCC", "RVHL", "INDBANK", "RENUKA", "DAMODARIND", "UJJIVANSFB", "SUZLON", "ORIENTPPR", "HINDCON", "NKIND", "BRNL", "ATL", "MAGNUM", "MOREPENLAB", "ORIENTCER", "MICEL", "ESAFSFB", "DEN", "TRU", "UTKARSHBNK", "FILATEX", "ROML", "HMAAGRO", "PCJEWELLER", "MODTHREAD", "MBLINFRA", "OBCL", "VARDHACRLC", "MANAKSTEEL", "ONEPOINT", "UCOBANK", "AROGRANITE", "DCW", "SUTLEJTEX", "BCLIND", "COFFEEDAY", "HMT", "BVCL", "RADHIKAJWE", "NSLNISP", "QGOLDHALF", "VINEETLAB", "LOTUSEYE", "NOVAAGRI", "BIOFILCHEM", "SPLIL", "PSB", "VLEGOV", "KOTARISUG", "PNC", "GULFPETRO", "IFCI", "MAHESHWARI", "SIGACHI", "SELMC", "KARMAENG", "ALLCARGO", "IRBINVIT", "ARTNIRMAN", "CENTRALBK", "PATELENG", "SADHNANIQ", "SHAHALLOYS", "PENINLAND", "KHAICHEM", "IRB", "ARIHANTCAP", "GTECJAINX", "MAHABANK", "INDTERRAIN", "HOVS", "IOB", "COMSYN", "AMDIND", "BALAJITELE", "MEGASOFT", "LLOYDSENGG", "SCILAL", "EDELWEISS", "MANAKCOAT", "MUKTAARTS", "ADVANIHOTR", "SNOWMAN", "NACLIND", "VASCONEQ", "SURYALAXMI", "TERASOFT", "USK", "MARALOVER", "MSUMI", "ABAN", "KREBSBIO", "PAISALO", "EGOLD", "ASIANTILES", "PARACABLES", "ABMINTLLTD", "SUMIT", "RPPL", "IRISDOREME", "PARADEEP", "GFLLIMITED", "MASKINVEST", "BYKE", "NITCO", "RTNINDIA", "ONMOBILE", "TARMAT", "DCM", "MMTC", "JISLJALEQS", "IDFCFIRSTB", "GMRP&UI", "BODALCHEM", "IMAGICAA", "WEWIN", "DWARKESH", "KHAITANLTD", "TEXMOPIPES", "SPIC", "TTML", "INTLCONV", "AGSTRA", "ELGIRUBCO", "MRO-TEK", "RADIANTCMS", "CONFIPET", "BROOKS", "DIGJAMLMTD", "RAJSREESUG", "MOL", "NETWORK18", "JMFINANCIL", "UMAEXPORTS", "SBFC", "MUNJALAU", "GHCLTEXTIL", "PIGL", "UGARSUGAR", "TRACXN", "IDBI", "GILLANDERS", "ALPA", "AVTNPL", "TNPETRO", "SERVOTECH", "SPENCERS", "CLEDUCATE", "SHRADHA", "SIGIND", "UNITEDPOLY", "MANALIPETC", "PLAZACABLE", "CTE", "BLKASHYAP", "SILVER", "NRL", "BANKA", "PODDARHOUS", "BANARBEADS", "SUPREMEINF", "GMRINFRA", "ADL", "WINDMACHIN", "SATINDLTD", "NDLVENTURE", "GEEKAYWIRE", "TPLPLASTEH", "UMANGDAIRY", "SAH", "CPSEETF", "JAGRAN", "OMAXE", "SHIVAMILLS", "MODIRUBBER", "CUPID", "EXXARO", "PGINVIT", "PDMJEPAPER", "ACLGATI", "DHRUV", "AUSOMENT", "AYMSYNTEX", "RKEC", "CUBEXTUB", "SARLAPOLY", "PFOCUS", "STEELCITY", "DELTAMAGNT", "GSS", "HPAL", "PANSARI", "MANAKSIA", "EQUITASBNK", "ACL", "HBSL", "SUVEN", "MAHASTEEL", "MADRASFERT", "KELLTONTEC", "RADIOCITY", "SIKKO", "GEOJITFSL", "ZIMLAB", "NHPC", "BPL", "EMAMIREAL", "SECMARK", "APOLLO", "NAVKARCORP", "SANGHIIND", "HMVL", "BEPL", "ALEMBICLTD", "GATEWAY", "NIITLTD", "RGL", "EMMBI", "TOTAL", "BLISSGVS", "KANPRPLA", "BHINVIT", "RBA", "JAYBARMARU", "MANGALAM", "LYKALABS", "TTL", "JMA", "BHAGYANGR", "CAMLINFINE", "PNBGILTS", "BHARATGEAR", "TBZ", "ORIENTLTD", "SHREDIGCEM", "TOKYOPLAST", "ARCHIDPLY", "JAYSREETEA", "ICICIB22", "HECPROJECT", "HFCL", "WORTH", "NFL", "SHRIRAMPPS", "IDFC", "AAATECH", "HILTON", "TIMESGTY", "ZODIACLOTH", "XELPMOC", "EMAMIPAP", "ESTER", "KRITINUT", "CAPTRUST", "KANORICHEM", "SATIA", "MANGCHEFER", "SINCLAIR", "RAJTV", "PANACHE", "BALPHARMA", "INDSWFTLAB", "AVROIND", "WEIZMANIND", "GOLDTECH", "VISAKAIND", "DEVIT", "MAWANASUG", "XCHANGING", "AUTOIND", "CANBK", "ISFT", "J&KBANK", "FEDFINA", "VETO", "SEQUENT", "INDOAMIN", "BALAXI", "UFO", "ANDHRSUGAR", "BANKINDIA", "SDBL", "PALREDTEC", "RATNAVEER", "MENONBE", "MODISONLTD", "ALKALI", "PNB", "SBGLP", "ISMTLTD", "TRIGYN", "DONEAR", "RUCHIRA", "JAMNAAUTO", "LOVABLE", "KOTHARIPRO", "MUFIN", "RBZJEWEL", "AHLADA", "HITECH", "YATRA", "AVONMORE", "RPPINFRA", "SOUTHWEST", "HIMATSEIDE", "CINELINE", "ALMONDZ", "SJVN", "INDIGRID", "PANACEABIO", "PALASHSECU", "EIFFL", "NAHARINDUS", "NXST", "STLTECH", "RICOAUTO", "GREAVESCOT", "KOTHARIPET", "LORDSCHLO", "DELTACORP", "TEXINFRA", "SINTERCOM", "INTENTECH", "IBREALEST", "EKC", "DCBBANK", "PRECWIRE", "SIMPLEXINF", "MITCON", "AARVI", "MAANALU", "BOROSCI", "MARINE", "WELSPUNLIV", "INOXGREEN", "ASIANHOTNR", "LAGNAM", "AHLEAST", "THEINVEST", "ORIENTHOT", "STCINDIA", "NELCAST", "AURUM", "LEMONTREE", "SAURASHCEM", "WSI", "UNIONBANK", "INOXWIND", "OMAXAUTO", "VALIANTLAB", "PRITI", "SOMICONVEY", "BANSWRAS", "CUB", "DOLATALGO", "ADSL", "AEROFLEX", "AIROLAM", "SHALPAINTS", "HPIL", "SAIL", "NAVNETEDUL", "HEXATRADEX", "FOODSIN", "CESC", "GAEL", "SHEMAROO", "REFEX", "KOKUYOCMLN", "CYBERTECH", "KRONOX", "VAISHALI", "DBOL", "PPLPHARMA", "FOCUS", "GANGESSECU", "SICALLOG", "NBCC", "SPMLINFRA", "GPTHEALTH", "TOUCHWOOD", "KUANTUM", "LAMBODHARA", "WANBURY", "MUNJALSHOW", "MARKSANS", "BIRLAMONEY", "GANESHBE", "PRSMJOHNSN", "TREJHARA", "GOKULAGRO", "UNIENTER", "WIPL", "PYRAMID", "BHAGERIA", "ZEEL", "MUKANDLTD", "INDOBORAX", "RAIN", "NYKAA", "RCF", "MUFTI", "MOTHERSON", "IOC", "UCAL", "ELIN", "GTPL", "ELECTCAST", "IITL", "RAMAPHO", "GRMOVER", "SMCGLOBAL", "KEYFINSERV", "PARKHOTELS", "IBULHSGFIN", "TAINWALCHM", "FEDERALBNK", "PRAKASH", "DCAL", "SPECIALITY", "OMINFRAL", "MOTISONS", "MAHAPEXLTD", "MAHEPC", "TVSSCS", "IRFC", "JTEKTINDIA", "LTF", "RHL", "SRM", "IEX", "BOMDYEING", "PENIND", "DEEPENR", "DEVYANI", "IREDA", "KRITI", "KALAMANDIR", "MANOMAY", "VERANDA", "ARTEMISMED", "TFCILTD", "TATASTEEL", "PARAGMILK", "SHIVATEX", "RSWM", "ZOMATO", "RSSOFTWARE", "SAMHI", "NATIONALUM", "MANAPPURAM", "HINDOILEXP", "KECL", "ORBTEXP", "BSL", "DELPHIFX", "ARVEE", "VPRPL", "EPL", "TARC", "JOCIL", "HISARMETAL", "BANDHANBNK", "ZUARI", "REPL", "IVP", "PRECAM", "AGRITECH", "SABTNL", "APCL", "BSHSL", "HEMIPROP", "SHREEPUSHK", "GLOBAL", "GPPL", "SHK", "KESORAMIND", "DBREALTY", "PLATIND", "PPAP", "NATHBIOGEN", "HARRMALAYA", "DCMNVL", "CASTROLIND", "RELINFRA", "UNIVASTU", "MANINFRA", "FSL", "SURYODAY", "GANDHAR", "PRIMESECU", "KARURVYSYA", "DTIL", "SMLT", "KITEX", "SMSPHARMA", "NAHARPOLY", "GULPOLY", "SUNFLAG", "TEXRAIL", "PTC", "LFIC", "MHLXMIRU", "GSLSU", "SSWL", "CGCL", "EPACK", "RUBYMILLS", "IRIS", "ATAM", "THOMASCOOK", "SUPERHOUSE", "SVLL", "CLSEL", "MRPL", "GLOBALVECT", "CANTABIL", "HITECHCORP", "THEMISMED", "INDIACEM", "WALCHANNAG", "STARCEMENT", "RELIGARE", "KTKBANK", "HEIDELBERG", "GAIL", "IIFLSEC", "ENIL"]
    df = pd.DataFrame(seg, columns=["SYMBOL \n"])
    #df = pd.read_csv("All-Companies.csv")
    st.write("*All Companies*")
    filtered_df = data_filter(df, stock_detail_df)
    finder(filtered_df)
