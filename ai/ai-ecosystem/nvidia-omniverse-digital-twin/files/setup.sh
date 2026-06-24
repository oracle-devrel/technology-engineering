PRIVATE_IP=$(ip route get 1 | sed 's/^.*src \([^ ]*\).*$/\1/;q')
PUBLIC_IP=$(curl ipinfo.io/ip)

sed -e "s/127.0.0.1/${PRIVATE_IP}/g" .env_template > .env

cat <<EOF | git apply
diff --git a/compose.yml b/compose.yml
index b89118a..06bed98 100644
--- a/compose.yml
+++ b/compose.yml
@@ -7,7 +7,9 @@ services:
       dockerfile: kit-app/Dockerfile
       network: host
     privileged: true
-    network_mode: host 
+    networks:
+      outside:
+        ipv4_address: ${PUBLIC_IP}
     ports:
       - "1024:1024/udp"
       - "49100:49100/tcp"
@@ -52,8 +54,8 @@ services:
       NGC_API_KEY: "\${NGC_API_KEY}"
     network_mode: host
     ipc: host
-    ports: 
-      - "8080:8080"
+    # ports:
+    #   - "8080:8080"
   zmq:
     image: "rtdt-zmq-service:latest"
     restart: unless-stopped
@@ -73,3 +75,11 @@ services:
 volumes:
   ov-cache:
   ov-local-share:
+
+networks:
+  outside:
+    driver: bridge
+    ipam:
+      driver: default
+      config:
+        - subnet: ${PUBLIC_IP%.*}.0/24
EOF
