/*
Copyright (c) 2024 Oracle and/or its affiliates.

The Universal Permissive License (UPL), Version 1.0

Subject to the condition set forth below, permission is hereby granted to any
person obtaining a copy of this software, associated documentation and/or data
(collectively the "Software"), free of charge and under any and all copyright
rights in the Software, and any and all patent rights owned or freely
licensable by each licensor hereunder covering either (i) the unmodified
Software as contributed to or provided by such licensor, or (ii) the Larger
Works (as defined below), to deal in both

(a) the Software, and
(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
one is included with the Software (each a "Larger Work" to which the Software
is contributed by such licensors),

without restriction, including without limitation the rights to copy, create
derivative works of, display, perform, and distribute the Software and make,
use, sell, offer for sale, import, export, have made, and have sold the
Software and the Larger Work(s), and to sublicense the foregoing rights on
either these or other terms.

This license is subject to the following condition:
The above copyright notice and either this complete permission notice or at
a minimum a reference to the UPL must be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

const fs = require('fs');
const oracledb = require('oracledb');
const http = require("http");
const express = require('express');
const app = express();
const path = require('path');

const password = process.env.ATP_PWD;
console.log("atp password:" + password);

oracledb.initOracleClient({ libDir: '/instantclient_23_3', configDir: '/instantclient_23_3/network/admin/' });

async function init() {
  try {
    // Create a connection pool which will later be accessed via the
    // pool cache as the 'default' pool.
    await oracledb.createPool({
      user: 'admin',
      password: password,
      connectString: 'atp_tp'
    });
    console.log('Connection pool started succesfully.'); 
  } catch (err) {
    console.error('init() error: ' + err.message);
    console.log('priceadmin/atp_pwd');
  }
}

app.get('/', (req, res) => {
  getSodaDoc().then((json) => {
     console.log(json);
     res.send(json);
  });
});

async function getSodaDoc() {
  let connection;
  try {
    // Get a connection from the default pool
    connection = await oracledb.getConnection();
    const soda = connection.getSodaDatabase();
    var collection = await soda.createCollection("hotel_reservations"); 
    collection = await soda.openCollection("hotel_reservations");
    const json = {
        "reservation_id": "2",
        "hotel_id": "123",
        "room_id": "315",
        "checkin_date": "2023-06-15",
        "checkout_date": "2023-06-17",
        "num_adults": 1,
        "num_children": 0,
        "guest_name": {
            "first_name": "Ethan",
            "last_name": "Lee"
        },
        "guest_contact_info": {
            "email": "ethan.lee@example.com",
            "phone": "123-8106",
            "address": {
                "city": "Madrid",
                "country": "Spain"
            }
        },
        "total_cost": 350.00,
        "payment_status": "paid"
    }
    var document = await collection.insertOneAndGet(json);
    const key = document.key;
    document = await collection.find().key(key).getOne() ;
    const content = await document.getContent();
    return content;
  } catch (err) {
    console.error(err);
  } finally {
    if (connection) {
      try {
        // Put the connection back in the pool
        await connection.close();
      } catch (err) {
        console.error(err);
      }
    }
  }
}

async function closePoolAndExit() {
  console.log('\nTerminating');
  try {
    await oracledb.getPool().close(10);
    console.log('Pool closed');
    process.exit(0);
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

process
  .once('SIGTERM', closePoolAndExit)
  .once('SIGINT',  closePoolAndExit);

init();
app.listen(3000);