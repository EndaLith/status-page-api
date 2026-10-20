from sqlalchemy import create_engine,text
from dotenv import load_dotenv 
import os 


load_dotenv() 
 

url= os.getenv("DATABASE_URL") 
print(url is not None) 

engine=create_engine(url) 
with engine.connect()as conn: 
    result=conn.execute(text("SELECT 1")) 
    print(result.scalar()) 

