import streamlit as st
import requests
import base64
import xml.etree.ElementTree as ET
import pandas as pd
from io import StringIO

st.set_page_config(page_title="INTELLISCAN Report Viewer", layout="wide")
st.title("🧠 INTELLISCAN Search Center")

# Shared Input Fields
env_url = st.text_input("🌐 Environment URL (e.g. https://iavnqy-test.fa.ocs.oraclecloud.com)", "")
username = st.text_input("👤 Username", "")
password = st.text_input("🔑 Password", type="password")
search_term = st.text_input("🔍 Search by full or partial OBJ_NAME or DATA:")

# Shared SOAP fetch function
def fetch_report(env_url, username, password, report_path):
    full_url = env_url.rstrip("/") + "/xmlpserver/services/ExternalReportWSSService"
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "Authorization": f"Basic {encoded_credentials}"
    }

    soap_request = f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:pub="http://xmlns.oracle.com/oxp/service/PublicReportService">
       <soap:Header/>
       <soap:Body>
          <pub:runReport>
             <pub:reportRequest>
                <pub:attributeFormat>csv</pub:attributeFormat>
                <pub:flattenXML>false</pub:flattenXML>
                <pub:reportAbsolutePath>{report_path}</pub:reportAbsolutePath>
                <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
             </pub:reportRequest>
          </pub:runReport>
       </soap:Body>
    </soap:Envelope>
    """

    response = requests.post(full_url, data=soap_request, headers=headers)

    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            report_bytes_elem = root.find('.//{http://xmlns.oracle.com/oxp/service/PublicReportService}reportBytes')

            if report_bytes_elem is not None and report_bytes_elem.text:
                report_decoded = base64.b64decode(report_bytes_elem.text).decode("utf-8")
                return report_decoded
            else:
                st.error("Connected but reportBytes is missing or empty.")
                st.code(response.content.decode("utf-8"), language="xml")
                return None
        except Exception as e:
            st.error("Error while decoding report:")
            st.exception(e)
            return None
    else:
        st.error(f"Request failed with status code: {response.status_code}")
        st.code(response.content.decode("utf-8"), language="xml")
        return None

# Tabs for two reports
tab1, tab2 = st.tabs(["📘 LOOKUP & VALUESET Search", "📗 FAST FORMULA Search"])

with tab1:
    st.subheader("📘 LOOKUP & VALUESET Report")
    if st.button("📥 Fetch LOOKUP Report"):
        if env_url and username and password:
            report_csv = fetch_report(env_url, username, password, 
                "/Custom/Human Capital Management/Sample Reports/INTELLISCAN REPORT.xdo")

            if report_csv:
                df = pd.read_csv(StringIO(report_csv))
                df.columns = [col.strip().upper() for col in df.columns]
                for col in ['OBJ_TYPE', 'OBJ_NAME', 'DATA']:
                    if col not in df.columns:
                        df[col] = ""

                if search_term:
                    search_upper = search_term.upper()
                    df = df[df["OBJ_NAME"].str.upper().str.contains(search_upper) | df["DATA"].str.upper().str.contains(search_upper)]

                st.success(f"✅ Fetched {len(df)} matching records.")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("❌ Could not fetch or decode the report.")
        else:
            st.warning("⚠️ Please fill in all fields before fetching the report.")

with tab2:
    st.subheader("📗 FAST FORMULA Report")
    if st.button("📥 Fetch FAST FORMULA Report"):
        if env_url and username and password:
            report_csv = fetch_report(env_url, username, password, 
                "/Custom/Human Capital Management/Sample Reports/FF INTELLISCAN REPORT.xdo")

            if report_csv:
                df = pd.read_csv(StringIO(report_csv))
                df.columns = [col.strip().upper() for col in df.columns]
                for col in ['OBJ_TYPE', 'OBJ_NAME', 'DATA']:
                    if col not in df.columns:
                        df[col] = ""

                if search_term:
                    search_upper = search_term.upper()
                    df = df[df["OBJ_NAME"].str.upper().str.contains(search_upper) | df["DATA"].str.upper().str.contains(search_upper)]

                st.success(f"✅ Fetched {len(df)} matching records.")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("❌ Could not fetch or decode the report.")
        else:
            st.warning("⚠️ Please fill in all fields before fetching the report.")
