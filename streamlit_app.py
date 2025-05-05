import streamlit as st
import altair as alt
import pandas as pd
import datetime

CSV_ENCODING:str = 'utf16'
CSV_SEP:str      = '\t'

KEY_DATE        = 'date'
KEY_TTVZ_MEMBER = 'name'
KEY_NUKI_ACTION = 'action'

def main() -> None:
    st.set_page_config(page_title="Nuki Data Statistics", layout="wide", page_icon=":material/thumb_up:")
    st.title(body="Nuki Access Data", help='Statistical Infos for Nuki Access at Tischtennisgarage')
    
    uploaded_file = st.file_uploader(label="Upload your Nuki access data .csv file", type=["csv"], help='select a locally present correct nuki access log file')
    if uploaded_file is not None:
        df:pd.DataFrame = pd.read_csv(filepath_or_buffer=uploaded_file, sep=CSV_SEP, encoding=CSV_ENCODING)
        df = df[[KEY_DATE, KEY_TTVZ_MEMBER, KEY_NUKI_ACTION, 'trigger', 'state', 'autoUnlock']]
        # take trigger instead of empty name
        df.name = df.name.fillna(value=df.trigger)

        SHOW_ENTRIES = 10
        st.subheader(body=f'Preview newest {SHOW_ENTRIES} log entries')
        st.write(df.head(n=SHOW_ENTRIES))

        st.subheader(body='Filter Date Range')
        first_date, last_date = df.date.loc[[len(df)-1,0]]

        col_from, col_to = st.columns(spec=[1,1])
        DATE_FORMAT = 'YYYY-MM-DD'
        with col_from:
            from_date = st.date_input(label='From Date', value=first_date, format=DATE_FORMAT, help='select from date').isoformat()
        with col_to:
            # adding one day to tte to_date to have really all data of the given day otherwise eg. from 2025-01-31 to 2025-01-31 would be empty 
            to_date   = (st.date_input(label='To Date',   value=last_date,  format=DATE_FORMAT, help='select to date') + datetime.timedelta(days=1)).isoformat()
        df = df[(df.date >= from_date) & (df.date <= to_date)]

        filtered_df = df
        # for now no additional filtering will be done
        if False:
            st.subheader(body='Filter Specific Data')
            columns         = df.columns.tolist()
            columns.remove('date') # date is the main selector and already handled above
            selected_column = st.selectbox('Select Column to filter by', columns)
            unique_values   = df[selected_column].unique()
            selected_value  = st.selectbox('Select value', unique_values)

            filtered_df = df[df[selected_column] == selected_value]
        st.metric(label="Current Number Of Records:", value=len(filtered_df), help='Nunber of records in selected date range')
        st.write(filtered_df)
                
        st.subheader(body=f'Nuki Access Statistics Chart Per Name From {from_date} To {to_date}')
        df_grouped_by_name = df.groupby(KEY_TTVZ_MEMBER, as_index=False).count() # we need index as normal column for alt.Chart()
        total_number_of_actions = sum(df_grouped_by_name[KEY_NUKI_ACTION])
        total_number_of_members = len(df_grouped_by_name)
        if st.button(label='Generate Name Bar Chart'):
            chart = alt.Chart(data=df_grouped_by_name[:]).mark_bar().encode(
                alt.X(shorthand=KEY_NUKI_ACTION
                    , title=f'Nuki Accesses: {total_number_of_actions}'
                    #, axis=alt.Axis(ticks=False, tickMinStep=10) # don't know for what
                ),
                alt.Y(shorthand=KEY_TTVZ_MEMBER
                    , sort='-x'
                    , title=f'TTVZ Members + Some Memberless Triggers: {total_number_of_members}'
                ),
                #color=alt.value("red"), # works (default is blue)
                alt.Color(shorthand=KEY_NUKI_ACTION, type='nominal', legend=None), # legend with different colors for given key
            ).properties(
                height=alt.Step(30) # default 20
                )
            st.write(chart)

        st.subheader(body=f'Nuki Access Statistics Chart Per Date From {from_date} To {to_date}')
        TZ='Europe/Zurich' # need local timezone (Zurich) for dates
        # modifying df.date to only have dates without times. Otherwise every date/time entry will be broken down to seconds level (we want day level)
        df.date = pd.to_datetime(df.date, utc=True).map(lambda x: x.tz_convert(TZ)).dt.date.astype(str)
        df_grouped_by_date = df.groupby(by=df.date, group_keys=False, as_index=False).count()
        total_number_of_actions = sum(df_grouped_by_date[KEY_NUKI_ACTION])
        total_number_of_dates   = len(df_grouped_by_date)
        if st.button(label='Generate Date Bar Chart'):
            chart = alt.Chart(data=df_grouped_by_date[:]).mark_bar().encode(
                alt.Y(shorthand=KEY_NUKI_ACTION
                    , title=f'Nuki Accesses: {total_number_of_actions}'
                ),
                alt.X(shorthand=KEY_DATE
                    , title=f'Dates: {total_number_of_dates}'
                ),
                alt.Color(shorthand=KEY_NUKI_ACTION, type='nominal', legend=None), # legend with different colors for given key
            )
            st.write(chart)

if __name__ == "__main__":
    # run it via streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false
    main()    
# end main
