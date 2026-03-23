css = '''
<style>

'''

bot_template = '''
<div style='display:flex;align-items:center;justify-content:flex-end;margin-bottom:10px;'>
                     <div style='background-color:{st.get_option("theme.secondaryBackgroundColor")};border-radius:10px;padding:10px;'>
                     <p style='margin:0;font-weight:bold;'>'EvaluationBot'</p>
                     <p style='margin:0;color={st.get_option("theme.textColor")}'>{{MSG}}</p>
                     </div>
                     <img src='https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frpj5kvxryk1/b/erpSQLTemplateDemo/o/images/personIcon.png' style='width:50px;height:50px;border-radius:50%;margin-left:10px;'>
                     </div>
'''

user_template = '''
<div style='display:flex;align-items:center;margin-bottom:10px;'>
                    <img src='https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frpj5kvxryk1/b/erpSQLTemplateDemo/o/images/botIcon.png' style='width:50px;height:50px;border-radius:50%;margin-right:10px;'>
                    <div style='background-color:st.get_option("theme.backgroundColor");{st.get_option("theme.secondaryBackgroundColor")};border-radius:10px;padding:10px;'>
                    <p style='margin:0;font-weight:bold;'>'Assistant'</p>
                    <p style='margin:0;color={st.get_option("theme.textColor")}'>{{MSG}}</p>
                    </div>
                    </div>
'''