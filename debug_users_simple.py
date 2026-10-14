from app.database import SessionLocal
from app.models import User
db = SessionLocal()
print(f'User count: {db.query(User).count()}')
db.close()
