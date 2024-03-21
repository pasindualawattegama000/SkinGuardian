from werkzeug.security import generate_password_hash

# Replace 'admin_password_here' with your actual password
hashed_password = generate_password_hash('thisIsAdmin1')
print(hashed_password)
