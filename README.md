# Laporan Modul 1 - CI/CD 
# Open Recruitment Admin Netics 2026

---
## Identity

Puspita Wijayanti Kusuma  
5025241059

---

## Soal 1

> Buatlah API publik dengan endpoint `/health` yang menampilkan informasi sebagai berikut:
> 
> ```json
> {
>   "nama": "Sersan Mirai Afrizal",
>   "nrp": "5025241999",
>   "status": "UP",
>   “timestamp”: time // Current time
>   "uptime": time  // Server uptime 
> }
> ```

Pada soal ini diminta untuk membuat API yang nantinya akan menghasilkan informasi berisi info pribadi dengan format JSON. Untuk mengerjakan soal ini saya membuat sebuah file [main.py](/src/main.py) menggunakan bahasa pemrograman python dan library `Flask` karena lebih familiar di deployment sebuah server. Berikut adalah rincian logic dari kode API yang telah saya buat:

```py
from flask import Flask
from datetime import datetime, timezone

app = Flask(__name__)


start_time = datetime.now(timezone.utc)

@app.route("/health")
def health_check():
    now = datetime.now(timezone.utc)
    
    totalSecs = int((now - start_time).total_seconds())
    
    hr = totalSecs // 3600
    result = totalSecs % 3600
    min = result // 60
    sec = result % 60
    
    uptime_format = f"{hr:02d}:{min:02d}:{sec:02d}"
    
    timeNow = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "nama": "Puspita Wijayanti Kusuma",
        "nrp": "5025241059", 
        "status": "UP",
        "timestamp": timeNow,
        "uptime": uptime_format
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

```
Berikut adalah penjelasan dari code tersebut:   
Untuk mengkonfigurasi servernya saya menggunakan framework `Flask` untuk membuat aplikasi APInya. Kemudian API di dijalankan di port 3000 pada `host="0.0.0.0"` agar API nya bisa diakses publik saat di-deploy ke server VPS. Selain itu untuk menghitung waktunya saya memakai perhitungan matematis  seperti yang terlihat di atas. Ketika `main.py` dijalankan nantinya akan mereturn informasi pribadi di atas.



## Soal 2
> Lakukan deployment API tersebut di dalam container pada VPS publik. Gunakan port selain 80 dan 443 untuk menjalankan API. 

Di soal no 2 ini targetnya melanjutkan soal no 1 tadi, di mana API tadi dideploy ke VPS publik menggunakan docker container. Di soal ini saya menggunakan port 3000 untuk menjalankan API nya sehingga nanti akan menjadi url `http://IP_VM:3000/health`. Namun mulai soal ini perlu mengkonfigurasi VPS terlebih dahulu di mana saat ini saya menggunakan VPS dari Azure.  
![vps-azure](/media/my-lowcost-vm.png)

### Docker Preparation on VPS
Pertama sebelum menjalankan dockernya perlu di-set up terlebih dahulu di bagian VPS.  
![install-docker](/media/install-docker.png)  

Kemudian file-file lokal yang telah dibuat tadi seperti `Dockerfile` dan `main.py`  perlu diupload ke VPS. Untuk upload file-filenya saya menggunakan command `scp -i ~/netics-modul1/netics-key.pem -r penugasan-modul1 azureuser@70.153.137.19:~`.  

Selanjutnya adalah build docker imagenya dengan command `docker build -t netics-health-api .` pada workdir `/penugasan-modul1` di VPS. Setelah image sudah ada perlu menjalankan container di port 3000 dengan command `docker run -d --name netics-api -p 3000:3000 netics-health-api`. 
![build-image-docker](/media/build-image-docker.png)  
![run-container](/media/run-container.png)  


### Result
endpoint `/health` pada alamat `http://70.153.137.19:3000/health` bisa diakses di browser.
![](/media/[2]%20run-terminal.png)
![](/media/[2]%20tes.png)


## Soal 3
> Gunakan Ansible untuk menginstall dan meletakkan konfigurasi nginx pada VPS. Nginx akan berperan sebagai reverse proxy yang meneruskan request ke API. Sehingga, API harus bisa diakses hanya dengan menjalankan Ansible Playbook tanpa intervensi/konfigurasi nginx secara manual. 

Pada soal ini diminta untuk menggunakan Ansible agar nginx tidak dijalankan secara manual. Jadi, di soal ini saya membuat 3 file, yaitu `nginx.conf.j2` untuk konfigurasi nginx nya, `site.yml` untuk set up nginx nya, serta `inventory.ini` sebagai ansible playbook. 

-  `inventory.ini`
    ```ini
    [vps]
    azure ansible_host=70.153.137.19 ansible_user=azureuser ansible_ssh_private_key_file=~/netics-modul1/netics-key.pem
    ``` 
    Jadi baris konfigurasi inventory Ansible ini mendefinisikan parameter koneksi ke VPS yang diberi alias azure. Selain itu secara spesifik juga menginstruksikan ansible untuk melakukan remote access ke alamat IP `70.153.137.19` menggunakan username `azureuser`, serta melakukan autentikasi secara otomatis tanpa password dengan menggunakan credential private key SSH yang berlokasi di local path `~/netics-modul1/netics-key.pem`.

- `nginx.conf.j2`

    ```
    server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location /health {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    } 
    
    ```
    Konfigurasi nginx ini berfungsi sebagai default server di port 80 serta menjadi reverse proxy. Jadi semua request yang masuk ke endpoint `/health` akan langsung di-forward ke lokal di port 3000. Selain itu di konfigurasi nginx terdpat parameter header, seperti `X-Real-IP` dan `X-Forwarded-For`, di mana data IP asli klien akan diteruskan oleh Nginx menuju backend, sehingga memastikan API menerima alamat IP klien dan bukan IP internal milik Nginx. 


- `site.yml`
    ```yml
    - name: setup nginx reverse proxy 
    hosts: vps
    become: true

    tasks:
        - name: install nginx
        apt:
            name: nginx
            state: present
            update_cache: true

        - name: copy nginx reverse proxy config
        template:
            src: nginx.conf.j2
            dest: /etc/nginx/sites-available/health-api

        - name: enable site
        file:
            src: /etc/nginx/sites-available/health-api
            dest: /etc/nginx/sites-enabled/health-api
            state: link
            force: true

        - name: restart nginx
        service:
            name: nginx
            state: restarted
            enabled: true
    ```
    File `site.yml` ini adalah skrip ansible playbook yang dipakai untuk mengkonfigurasi Nginx menjadi reverse proxy di VPS secara otomatis. Karena butuh akses root,  ditambahkan `become: true` di awal. Untuk proses kerjanya pertama, skrip ini akan menginstal Nginx lewat apt dan otomatis menjalankan update untuk mendapat package terbaru. Setelah itu, template konfigurasi lokal yaitu file `nginx.conf.j2` di-copy ke folder `/etc/nginx/sites-available/health-api` di server. Kemudian, agar konfigurasinya aktif, dibuat symlink ke folder `sites-enabled/`. Di bagian ini saya pakai opsi `force: true` untuk jaga-jaga kalau misal sebelumnya sudah ada symlink lama dan nanti akan ditimpa. Terakhir, file ini akan merestart Nginx agar aturan barunya langsung di-apply. Selain itu juga di-set `enabled: true` supaya Nginx-nya otomatis dimuat ulang setiap kali server di-reboot.

### Result
output terminal saat eksekusi playbook ansible untuk deployment nginx dengan kondisi docker container sudah dijalankan juga.
![img](/media/[3]%201.png)  
![img](/media/[3]%202.png)  

hasil di browser  
![img](/media/[3]%203.png)  


## Soal 4
> Lakukan proses CI/CD menggunakan GitHub Actions untuk melakukan otomasi proses deployment API. Terapkan juga best practices untuk menjaga kualitas environment CI/CD.

Pada soal ini diminta untuk membuat gitHub Actions yang otomatis build image Docker,deploy ke VPS, dan merestart container API. Untuk mengerjakan soal ini saya membuat file `ci-cd.yml` pada workdir `.github/workflows/ci-cd.yml`. 

```yml
name: ci-cd

on:
  push:
    branches:
      - main
  workflow_dispatch:

concurrency:
  group: deploy-production
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: checkout repository
        uses: actions/checkout@v4

      - name: setup python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: validate python syntax
        run: python -m py_compile src/main.py

      - name: build docker image
        run: docker build -t netics-health-api ./src

  deploy:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: checkout repository
        uses: actions/checkout@v4

      - name: copy project files to vps
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          source: "src,deploy.sh,README.md"
          target: "~/app"
          rm: true

      - name: deploy on vps
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            chmod +x ~/app/deploy.sh
            ~/app/deploy.sh

```
File `ci-cd.yml` ini berisi konfigurasi GitHub Actions untuk otomatisasi deploy ke VPS. Skrip ini diset agar otomatis dijalankan setiap ada push ke branch main atau saat terdapat trigger manual lewat `workflow_dispatch`. Di sini terdapat juga blok concurrency yang akan mengcancel proses lama dan menjalankan push yang paling baru  agar server tidak error karena menerima banyak antrian deploy. Alur kerjanya sendiri dibagi jadi dua job utama. Pertama terdapat job test yang dijalankan di server Ubuntu bawaan GitHub. Di sini, sistem akan clone repo sya menggunakan action `checkout`, menyiapkan environment Python 3.11, lalu mengecek sintaks `main.py` memakai `py_compile` untuk memastikan tidak ada error. Setelah itu, terdapat uji coba build image Docker lokal untuk ,mengecek apakah Dockerfile-nya aman dan work. Kalau job test tersebut berhasil maka dilanjutkan alurnya ke job deploy (karena ada aturan ``needs: test`). Di tahap ini, akan dibutuhkan data dari GitHub Secrets untuk login, lalu nge-copy file src, dan README.md ke folder `~/app` di VPS menggunakan modul `scp-action`. Terakhir, memakai modul `ssh-action` di mana sistem akan ngeremot terminal VPS, memberi akses executable ke file ci-cd.yml, dan langsung menjalankan script tersebut untuk merestart container API langsung dari dalam server.

## Preparation
Untuk menjalankan ci-cd nya, sebelumnya perlu mendapatkan beberapa credential untuk menjalankan github actions nya. 

1. generate SSH key khusus GitHub Actions  
    di terminal lokal dibuat SSH key baru yang dikhususkan untuk keperluan deploy saja. Command ini akan menghasilkan 2 file, yaitu file untuk private key (~/.ssh/netics_actions.pub) dan public key (~/.ssh/netics_actions.pub).  
    ```C
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/netics_actions -N ""
    ```
    ![](/media/[4]%201.png)  

2. menambahkan public key ke VPS  
    setelah key tersebut berhasil dibuat, public key tersebut disalin ke VPS agar GitHub Actions diberikan izin untuk masuk ke server. Command `ssh-copy-id` akan secara otomatis menambahkan public key ke file `~/.ssh/authorized_keys` di VPS.
    ```c
    ssh-copy-id -i ~/.ssh/netics_actions.pub azureuser@70.153.137.19
    ```

3. lalu menbuat konfigurasi folder SSH di VPS  
    selanjutnya masuk ke VPS dan menjalankan command di bawah untuk memastikan folder SSH secure dan untuk menghindari error connection karena masalah permission:
    ```c
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/authorized_keys
    ```

    ![](/media/[4].png)
    ![](/media/[4]%203.png)  

4. Menambahkan secrets ke github action  
    di state ini credentials yang telah dipunya diinsert ke github pada page actions (`/settings/secrets/actions`)
    
    ```
    VPS_HOST = 70.153.137.19
    VPS_USER = azureuser
    VPS_SSH_KEY = isi private key
    ```

    Isi private key didapat dari command berikut di terminal lokal:
    `cat ~/.ssh/netics_actions`

    ![](/media/[4]%202.png)  


5. commit project ke repository github
    pada state ini, setelah perubahan di-commit dan di-push ke branch main github, workflow deployment nya akan berjalan secara otomatis. Saat indikator di tab Actions statusnya success, endpoint API bisa langsung diakses menggunakan versi code terbaru tanpa perlu deploy manual.  
    ![](/media/[4]%204.png)  

### Result
http://70.153.137.19/health  
![](/media/[3]%203.png)  



## Credits and Citation
**Repository / Documentation**  
https://gist.github.com/unixcharles/949271  
https://github.com/oneuptime/blog/tree/master/posts/2026-02-21-ansible-configure-reverse-proxy-nginx  
https://flask.palletsprojects.com/en/stable/quickstart/  
https://github.com/appleboy/ssh-action
https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy  
https://github.com/arsitektur-jaringan-komputer/modul-ansible/blob/master/2.%20Ansible%20Playbook/README.md  
https://github.com/geerlingguy/ansible-role-nginx  

**Penggunaan AI**
![](/media/res-1.png)
![](/media/res-2.png)
![](/media/res-3.png)
![](/media/res-5.png)
![](/media/res-6.png)




    

