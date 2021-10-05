#!/usr/bin/env python
# coding: utf-8

# In[14]:


#Importing the required libraries
import pandas as pd
import numpy as np
import math
from datetime import date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# In[15]:


#Reading the sales data and inventory data into dataframes
sales_data=pd.read_excel('Zepto Case Study.xlsx',sheet_name='Sales Data')
inventory_data=pd.read_excel('Zepto Case Study.xlsx',sheet_name='Inventory Data')


# In[16]:


#Grouping the data into product level to extrac the total sales, sales start date and sales end date
product_sales=sales_data.groupby(['product_variant_id']).agg(total_sales=('quantity_sold','sum'),start_date=('business_date','min'),end_date=('business_date','max')).reset_index()


# In[17]:


#Caluculating the average sales perday for each SKU(Rate of Sales)
product_sales['no_days']=((product_sales['end_date']-product_sales['start_date']).dt.days)+1
product_sales['avg_sales']=product_sales['total_sales']/product_sales['no_days']


# In[18]:


product_sales


# In[19]:


#Joning the product level rate of sales dataframe to the inventory data
final_ads=pd.merge(inventory_data,product_sales,left_on='product_variant_id',right_on='product_variant_id',how='left')


# In[20]:


final_ads


# In[21]:


#Taking the maximum of lead time and review time to derive no of days for which order should be placed without OOS at product level 
final_ads['No_days_to_survive']=np.where(final_ads['Lead time ']>final_ads['Review time'],final_ads['Lead time '],final_ads['Review time'])
#Deriving the final  lo of days for which order should be placed by considering shelf life and lead time and taking the least value of both in orderto avoid wastage
final_ads['No_days_to_survive']=np.where(final_ads['No_days_to_survive']>(final_ads['Shelf life in days']+final_ads['Lead time ']),(final_ads['Shelf life in days']+final_ads['Lead time ']),final_ads['No_days_to_survive'])


# In[22]:


#Total stock is calculated by summing up the stock in hand, Qty in transit and Qty @ Warehouse
final_ads['total_stock']=final_ads['StockOnHand']+final_ads['Qty in Transit']+final_ads['Qty @ Warehouse']
#safety stock is calculated by considering that A+ SKUs should have 1 day rate of sale of extra total stock 
final_ads['safety_stock_needed']=np.where(np.logical_and((final_ads['Sku Classification']=='A+'),(final_ads['total_stock']<(2*final_ads['avg_sales']))),final_ads['avg_sales'],0)
#total stock needed is calculated by summing the safety stock needed and based on rateof sale and no of days to survive
final_ads['total_stock_needed']=(final_ads['avg_sales']*final_ads['No_days_to_survive'])+final_ads['safety_stock_needed']


# In[23]:


#Quantity to order is calculated based on difference between total stock and total stock needed
final_ads['Qty to order']=np.where(final_ads['total_stock_needed']-final_ads['total_stock']<0,0,(final_ads['total_stock_needed']-final_ads['total_stock']))
final_ads['Qty to order'] = final_ads['Qty to order'].apply(np.ceil)


# In[24]:


#Selecting the required columns
final_ads=final_ads[['product_variant_id', 'Description',
        'Shelf life in days','avg_sales','StockOnHand',  'Lead time ',
       'Review time', 'Qty in Transit', 'Qty @ Warehouse',
       'Qty to order']]
final_ads.rename(columns={'Shelf life in days':'Shelf life','avg_sales':'Rate of Sales'}, inplace = True)


# In[25]:


#Writing the csv to attach it later to a email
filename="Replenishment Schedule "+ str(date.today())+'.csv'
final_ads.to_csv(filename,index=False)


# In[26]:


#Code to send the file in email
fromaddr = "from email id"
toaddr = ", ".join(['to email ids'])
   
# instance of MIMEMultipart
msg = MIMEMultipart()
  
# storing the senders email address  
msg['From'] = fromaddr
  
# storing the receivers email address 
msg['To'] = toaddr
  
# storing the subject 
msg['Subject'] = "Assignment | Replenishment Schedule |"+ str(date.today())
  
# string to store the body of the mail
body = "Hi All,\nPFA the replenishment schedule for today"
  
# attach the body with the msg instance
msg.attach(MIMEText(body, 'plain'))
  
# open the file to be sent 

attachment = open(filename, "rb")
  
# instance of MIMEBase and named as p
p = MIMEBase('application', 'octet-stream')
  
# To change the payload into encoded form
p.set_payload((attachment).read())
  
# encode into base64
encoders.encode_base64(p)
   
p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
  
# attach the instance 'p' to instance 'msg'
msg.attach(p)
# creates SMTP session
s = smtplib.SMTP('smtp.gmail.com', 587)
  
# start TLS for security
s.starttls()
  
# Authentication
s.login(fromaddr, "your password")
  
# Converts the Multipart msg into a string
text = msg.as_string()
  
# sending the mail
s.sendmail(fromaddr, toaddr, text)
  
# terminating the session
s.quit()

