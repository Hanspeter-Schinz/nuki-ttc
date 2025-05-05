import streamlit as st
import altair as alt
import pandas as pd
import datetime

CSV_ENCODING:str = 'utf16'
CSV_SEP:str      = '\t'

TTVZ_MEMBER = 'name'
NUKI_ACTION = 'action'

st.set_page_config(page_title="Nuki Data Statistics", layout="wide", page_icon=":material/thumb_up:")

def main() -> None:
    st.title("Nuki Access Data")
    
    uploaded_file = st.file_uploader(label="Upload your Nuki access data .csv file", type=["csv"])
    
    if uploaded_file is not None:
        df:pd.DataFrame = pd.read_csv(filepath_or_buffer=uploaded_file, sep=CSV_SEP, encoding=CSV_ENCODING)
        df = df[['date', TTVZ_MEMBER, NUKI_ACTION, 'trigger', 'state', 'autoUnlock']]
        # take trigger instead of empty name
        df.name = df.name.fillna(value=df.trigger)

        SHOW_ENTRIES = 10
        st.subheader(body=f'Preview newest {SHOW_ENTRIES} log entries')
        st.write(df.head(n=SHOW_ENTRIES))

        st.subheader(body='Filter Date Range')
        #first_date = df.date.iloc[-1]
        #last_date  = df.date.iloc[0]
        first_date, last_date = df.date.loc[[len(df)-1,0]]
        #first_date, last_date = df.date.iloc[[-1,0]] # gives warnings but works
        #print(f'{first_date = }, {last_date = }')

        col_from, col_to = st.columns(spec=[1,1])
        FORMAT = 'YYYY-MM-DD'
        with col_from:
            from_date = st.date_input(label='From Date', value=first_date, format=FORMAT, help='select from date').isoformat()
        with col_to:
            # adding one day to tte to_date to have really all data of the given day otherwise eg. from 2025-01-31 to 2025-01-31 would be empty 
            to_date   = (st.date_input(label='To Date',   value=last_date,  format=FORMAT, help='select to date') + datetime.timedelta(days=1)).isoformat()
        # the next session does not work correctly st.date_input() does not change the default dates but data (df) does    
        #if st.button(label='Reset Dates'):
        #    from_date = first_date
        #    to_date   = last_date
        df = df[(df.date >= from_date) & (df.date <= to_date)]

        filtered_df = df
        # for now no additional filtering will be done
        if False:
            st.subheader(body='Filter Specific Data')
            columns         = df.columns.tolist()
            columns.remove('date')
            selected_column = st.selectbox('Select Column to filter by', columns)
            unique_values   = df[selected_column].unique()
            selected_value  = st.selectbox('Select value', unique_values)

            filtered_df = df[df[selected_column] == selected_value]
        st.metric("Current Number Of Records:", len(filtered_df))
        st.write(filtered_df)
                
        st.subheader(body='Nuki Access Statistics Chart')
        #df_grouped = df.groupby(TTVZ_MEMBER).count().sort_values(by=NUKI_ACTION, ascending=False)
        df_grouped = df.groupby(TTVZ_MEMBER, as_index=False).count() # we need index as normal column for alt.Chart()
        #df_grouped = df.groupby(TTVZ_MEMBER, as_index=False).count().sort_values(by=NUKI_ACTION, ascending=False).reset_index(drop=True)
        #df_grouped = df.groupby(TTVZ_MEMBER, as_index=False).count().reset_index(drop=True)
        #df_grouped.set_index(df_grouped.name)
        #print(f'{df_grouped = }')
        total_number_of_actions = sum(df_grouped[NUKI_ACTION])
        total_number_of_members = len(df_grouped)
        if st.button(label='Generate Bar Chart'):
            # wtf it is not sorted (seems to be a long during bug in bar_chart()) !!!!
            #st.bar_chart(data=df_grouped[:10],
            #    x=None, x_label=f'Nuki Accesses ({total_number_of_members})',
            #    #x=f'{TTVZ_MEMBER}', x_label=f'Nuki Accesses ({total_number_of_actions})',
            #    y=f'{NUKI_ACTION}', y_label=f'TTVZ Members + Some Memberless Triggers {total_number_of_members}',
            #    horizontal=True
            #    )

            chart = alt.Chart(data=df_grouped).mark_bar().encode(
                alt.X(shorthand=NUKI_ACTION
                    , title=f'Nuki Accesses: {total_number_of_actions}'
                    #, axis=alt.Axis(ticks=False, tickMinStep=10) # don't know for what
                ),
                alt.Y(shorthand=TTVZ_MEMBER
                    , sort='-x'
                    , title=f'TTVZ Members + Some Memberless Triggers: {total_number_of_members}'
                ),
                #color=alt.value("red"), # works (default is blue)
                #alt.Color(type='nominal'), # no idea for what ????
            )
            st.write(chart)

if __name__ == "__main__":
    # run it via streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false
    main()    
# end main
