# Linux Server Hardening Checklist

**Приоритет:** Выполнить ДО деплоя в production.

---

## 🔴 КРИТИЧНО (сделать первым делом)

### 1. SSH Hardening

```bash
# /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config
```

```
# Отключить root login
PermitRootLogin no

# Только ключи, без паролей
PasswordAuthentication no
PubkeyAuthentication yes

# Отключить пустые пароли
PermitEmptyPasswords no

# Ограничить пользователей
AllowUsers your_deploy_user

# Изменить порт (опционально, но полезно)
Port 2222

# Таймауты
ClientAliveInterval 300
ClientAliveCountMax 2

# Отключить X11 и агент форвардинг
X11Forwarding no
AllowAgentForwarding no
```

```bash
# Применить
sudo systemctl restart sshd
```

### 2. Firewall (UFW)

```bash
# Установить
sudo apt install ufw

# Дефолтные правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешить SSH (на новом порту если меняли)
sudo ufw allow 2026/tcp comment 'SSH'

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Включить
sudo ufw enable
sudo ufw status verbose
```

### 3. Fail2Ban (автобан атакующих)

```bash
# Установить
sudo apt install fail2ban

# Создать локальный конфиг
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8

[sshd]
enabled = true
port = 2222
maxretry = 3
bantime = 86400

# Nginx rate limit (парсит логи nginx)
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=nginx-limit-req, port="http,https"]
logpath = /var/log/nginx/error.log
findtime = 60
maxretry = 10
bantime = 3600
```

```bash
# Создать фильтр для nginx
sudo nano /etc/fail2ban/filter.d/nginx-limit-req.conf
```

```ini
[Definition]
failregex = limiting requests, excess:.* by zone.*client: <HOST>
ignoreregex =
```

```bash
# Запустить
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### 4. Автообновления безопасности

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🟠 ВАЖНО (сделать до production)

### 5. Отключить ненужные сервисы

```bash
# Посмотреть что слушает
sudo ss -tulpn

# Отключить ненужное
sudo systemctl disable cups
sudo systemctl disable avahi-daemon
sudo systemctl disable bluetooth
```

### 6. Ограничить sudo

```bash
# Создать отдельного пользователя для деплоя
sudo adduser deploy
sudo usermod -aG docker deploy

# Ограничить sudo только нужными командами
sudo visudo
```

```
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose
```

### 7. Защита /tmp и /var/tmp

```bash
# /etc/fstab — добавить noexec
tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev 0 0
tmpfs /var/tmp tmpfs defaults,noexec,nosuid,nodev 0 0
```

### 8. Kernel Hardening (sysctl)

```bash
sudo nano /etc/sysctl.d/99-security.conf
```

```ini
# Защита от IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Игнорировать ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Не отвечать на broadcast ping
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Защита от SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# Отключить IP forwarding (если не роутер)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Защита от smurf атак
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Логировать подозрительные пакеты
net.ipv4.conf.all.log_martians = 1
```

```bash
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

---

## 🟡 РЕКОМЕНДУЕТСЯ

### 9. Логирование и мониторинг

```bash
# Установить auditd
sudo apt install auditd

# Базовые правила аудита
sudo nano /etc/audit/rules.d/audit.rules
```

```
# Мониторинг sudo
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Мониторинг SSH
-w /etc/ssh/sshd_config -p wa -k sshd

# Мониторинг passwd/shadow
-w /etc/passwd -p wa -k passwd
-w /etc/shadow -p wa -k shadow
```

```bash
sudo systemctl restart auditd
```

### 10. Docker Hardening

```bash
# Не запускать контейнеры от root
# В docker-compose.yml добавить:
# user: "1000:1000"

# Ограничить ресурсы
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 2G

# Использовать read-only где возможно
# read_only: true
```

### 11. Бэкапы

```bash
# Cron для ежедневного бэкапа
sudo crontab -e
```

```
0 3 * * * /path/to/backup-script.sh >> /var/log/backup.log 2>&1
```

---

## 📋 Чек-лист перед деплоем

- [ ] SSH: root login отключен
- [ ] SSH: только ключи, без паролей
- [ ] SSH: порт изменён (опционально)
- [ ] UFW: включен, только 80/443/SSH
- [ ] Fail2Ban: настроен для SSH и nginx
- [ ] Автообновления: включены
- [ ] Ненужные сервисы: отключены
- [ ] sysctl: hardening применён
- [ ] Docker: не от root
- [ ] Бэкапы: настроены

---

## 🔧 Полезные команды

```bash
# Проверить открытые порты
sudo ss -tulpn

# Проверить fail2ban статус
sudo fail2ban-client status sshd

# Проверить UFW
sudo ufw status numbered

# Проверить логи auth
sudo tail -f /var/log/auth.log

# Проверить кто залогинен
who
last -10
```

---

## ⚠️ После настройки

1. **Проверить SSH доступ** перед закрытием текущей сессии
2. **Сохранить SSH ключи** в безопасном месте
3. **Документировать** изменённый порт SSH
4. **Протестировать** fail2ban (попробовать 5 неудачных SSH)
