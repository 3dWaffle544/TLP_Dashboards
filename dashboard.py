import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import altair as alt
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_TABLE = os.getenv('POSTGRES_TABLE')


count = st_autorefresh(interval=30000, key="dataframe_autorefresh")

connection_string = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

from sqlalchemy import create_engine
engine = create_engine(connection_string)
query = f"SELECT * FROM {POSTGRES_TABLE}"

##Read data from PostgreSQL
df = pd.read_sql(query, con=engine)


st.logo('https://www.trackloaderparts.com/static/version1752659053/frontend/Ey/trackloader/en_US/images/mobile-logo.png', size="large", link="https://trackloaderparts.com")
st.title('Ticket Overview')
st.write('Total Tickets: ' + str(len(df)))
st.write('Last updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

tab1, tab2, tab3 = st.tabs(['Ticket Overview', 'Ticket Type Distribution', 'Ticket Progress by Salesman'])

with tab1:
    st.subheader('5 Most Recent Tickets')
    st.write(df.sort_values(by='time_created', ascending=False).head(5))



with tab2:
    ticket_counts = df.pivot_table(
        index='ticket_type',
        aggfunc='size'
    ).reset_index(name='count')


    chart = alt.Chart(ticket_counts).mark_arc().encode(
        theta=alt.Theta(field='count', type='quantitative'),
        color=alt.Color(field='ticket_type', type='nominal'),
        tooltip=['ticket_type', 'count']
    ).properties(
        title='Ticket Type Distribution'
    )

    st.altair_chart(chart, use_container_width=True)


    ##Completion Chart

with tab3:
    time_filter = st.radio("Filter by time range:", ["Past Day", "Last 7 Days", "Last 30 Days","All Time"])

    # Filter by time
    now = datetime.now()
    if time_filter == "Past Day":
        cutoff = now - timedelta(days=1)
        df_filtered = df[df['time_created'] >= cutoff]
    elif time_filter == "Last 7 Days":
        cutoff = now - timedelta(days=7)
        df_filtered = df[df['time_created'] >= cutoff]
    elif time_filter == "Last 30 Days":
        cutoff = now - timedelta(days=30)
        df_filtered = df[df['time_created'] >= cutoff]
    else:
        df_filtered = df


    pivot_df = df_filtered.pivot_table(index='assigned_salesman_name', columns='ticket_progress', aggfunc='size', fill_value=0)
# Reset index and melt to long-form
    long_df = pivot_df.reset_index().melt(
        id_vars='assigned_salesman_name',
        var_name='Progress',
        value_name='Count'
    )

    # Custom color map
    color_map = alt.Scale(
        domain=['Completed', 'In Progress', 'Overdue', 'Pending'],
        range=['green', 'orange', 'red', 'aqua']
    )

    # Altair chart
    chart = alt.Chart(long_df).mark_bar().encode(
        x=alt.X('assigned_salesman_name:N', title='Salesman', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Count:Q', title='Ticket Count', axis=alt.Axis(labelAngle=0)),
        color=alt.Color('Progress:N', scale=color_map, legend=alt.Legend(title="Ticket Progress")),
        tooltip=['assigned_salesman_name', 'Progress', 'Count']
    ).properties(
        title='Ticket Progress by Salesman'
    )

    st.altair_chart(chart, use_container_width=True)
