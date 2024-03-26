from werkzeug.security import generate_password_hash


hashed_password = generate_password_hash('password123')
print(hashed_password)

# INSERT INTO `admins`( `email`, `password`) VALUES ('admin@gmail.com','scrypt:32768:8:1$nKKWCooHt62eWNU8$9f23dd7c78fcbb281536b1e3cf97fe4214fd98c75e0d9f50ba0fa7f0da60b54a56f5fc76d067358c01210f38e2de007d3bff93ac86c8b7091679c38fd55bfc98')