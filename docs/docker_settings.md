```bash
docker run -d \
  --name cityarkdb \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=citi123 \
  -v ~/mysql_data:/var/lib/mysql \
  mysql:8.0
```

```bash
docker exec -it cityarkdb bash
```

```sql
-- 新用户
CREATE USER 'cityark_user'@'%' IDENTIFIED BY 'cityark_passwd';
-- 新数据库
CREATE DATABASE cityark;
-- 授权
GRANT ALL PRIVILEGES ON cityark.* TO 'cityark_user'@'%';
```

