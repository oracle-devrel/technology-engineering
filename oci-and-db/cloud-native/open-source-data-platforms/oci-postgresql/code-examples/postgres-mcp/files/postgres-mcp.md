# Use PostgreSQL MCP Pro with OCI Database with PostgreSQL

The steps use PostgresQL MCP Pro, which can be found [here](https://github.com/crystaldba/postgres-mcp/tree/main).

**Prerequisites:**
- Oracle Linux VM
- Open correct ports (8000) on VM and in security lists
- Create PostgreSQL instance, with ```pg_stat_statements``` enabled.
- VScode and Cline installed


# Run PostgreSQL MCP Pro - steps

- Install/Start Docker
    ```
    sudo yum install -y yum-utils  
    sudo yum-config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
    sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl start docker
    ```

- Run the MCP server.
Change the user name, password, endpoint, and database in the below.
    ```
    sudo docker run -p 8000:8000 \
      -e DATABASE_URI=postgresql://[USER_NAME]:[PASSWORD]@[ENDPOINT]:5432/[DATABASE] \
      crystaldba/postgres-mcp --access-mode=unrestricted --transport=sse
    ```

    After running the above, you should see in part a response like:

  ```
      [03/26/26 08:17:29] INFO     Starting PostgreSQL MCP Server in     server.py:555
                                 UNRESTRICTED mode                                  
                        INFO     Successfully connected to database    server.py:568
                                 and initialized connection pool                    
    INFO:     Started server process [7]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    ```
    
# Cline, VSCode

- Install/Open Cline in your VSCode
- Add a new Remote Server with the option "SSE (Legacy)" checked. An example is:
  ```
  http://[PUBLIC_IP_INSTANCE]:8000/sse
  ```

# Example:

- Prompt:
    ```Review the health my postgresql database```
    
- Reply:
    ```
    I reviewed the PostgreSQL instance health and it looks generally healthy overall. The checks found no invalid, duplicate, bloated, or unused indexes; no invalid constraints; no transaction ID wraparound risk; and table buffer cache hit rate is strong at 99.4%. Connection usage also looks healthy with 12 total connections and none idle. There are no active replicas connected, so this appears to be operating as a primary without live replication.The one notable issue is __inactive logical replication slots__ retaining WAL: `XX` on database `XX` is retaining about __32 GB__ of WAL, and `XX` on `XXX` is retaining about __1.7 GB__. If these slots are no longer needed, they should be removed; if they are expected, the downstream consumers should reconnect and catch up. Left unattended, inactive slots can cause unnecessary disk growth. Also, index buffer cache stats were unavailable, which may simply mean insufficient collected stats rather than a problem. Recommended next step: validate whether those two slots are still required and clean them up if not.
```
