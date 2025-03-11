/*******************************************************************************
 * Copyright (c) 2025 Oracle and/or its affiliates. All rights reserved. DO NOT
 * ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
 *
 * The Universal Permissive License (UPL), Version 1.0
 *
 * Subject to the condition set forth below, permission is hereby granted to any
 * person obtaining a copy of this software, associated documentation and/or
 * data (collectively the "Software"), free of charge and under any and all
 * copyright rights in the Software, and any and all patent rights owned or
 * freely licensable by each licensor hereunder covering either (i) the
 * unmodified Software as contributed to or provided by such licensor, or (ii)
 * the Larger Works (as defined below), to deal in both
 *
 * (a) the Software, and
 *
 * (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
 * one is included with the Software each a "Larger Work" to which the Software
 * is contributed by such licensors),
 *
 * without restriction, including without limitation the rights to copy, create
 * derivative works of, display, perform, and distribute the Software and make,
 * use, sell, offer for sale, import, export, have made, and have sold the
 * Software and the Larger Work(s), and to sublicense the foregoing rights on
 * either these or other terms.
 *
 * This license is subject to the following condition:
 *
 * The above copyright notice and either this complete permission notice or at a
 * minimum a reference to the UPL must be included in all copies or substantial
 * portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *******************************************************************************/

CREATE TABLE OS_COUNTRY
  (COUNTRYCODE VARCHAR2(32 BYTE) NOT NULL ENABLE,
   COUNTRYNAME VARCHAR2(255 BYTE) NOT NULL ENABLE,
   CONSTRAINT OSCOUNTRY_PK PRIMARY KEY (COUNTRYCODE));

CREATE TABLE OS_ACCOUNT
  (USERID VARCHAR2(255 BYTE) NOT NULL ENABLE,
   USERNAME VARCHAR2(255 BYTE) NOT NULL ENABLE,
   FIRSTNAME VARCHAR2(255 BYTE),
   LASTNAME VARCHAR2(255 BYTE),
   PASSWORD VARCHAR2(255 BYTE),
   EMAIL VARCHAR2(255 BYTE) NOT NULL ENABLE,
   PROVISIONDATE DATE,
   STATUS VARCHAR2(32 BYTE),
   COUNTRYCODE VARCHAR2(32 BYTE),
   CONSTRAINT OSACCOUNT_PK PRIMARY KEY (USERID),
   CONSTRAINT OSCOUNTRY_FK FOREIGN KEY(COUNTRYCODE) REFERENCES OS_COUNTRY(COUNTRYCODE) ON DELETE CASCADE);

CREATE TABLE OS_HOST
  (HOSTID VARCHAR2(255 BYTE) NOT NULL ENABLE,
   HOSTNAME VARCHAR2(255 BYTE) NOT NULL ENABLE,
   CONSTRAINT OSHOSTS_PK PRIMARY KEY (HOSTID));

CREATE TABLE OS_ACCOUNT_HOST
  (USERID VARCHAR2(255 BYTE) NOT NULL ENABLE,
   HOSTID VARCHAR2(255 BYTE) NOT NULL ENABLE,
   CONSTRAINT OSACCOUNTHOST_PK PRIMARY KEY (USERID, HOSTID),
   CONSTRAINT OSACCOUNT_FK FOREIGN KEY(USERID) REFERENCES OS_ACCOUNT(USERID) ON DELETE CASCADE,
   CONSTRAINT OSHOST_FK FOREIGN KEY(HOSTID) REFERENCES OS_HOST(HOSTID) ON DELETE CASCADE);

/* NOTE: Below entries are provided as sample/reference only.
         Included names and dates are randomly generated and used fictitiously.
         Any resemblance to locales or persons, living or dead, is entirely coincidental. */

INSERT INTO OS_COUNTRY (COUNTRYCODE,COUNTRYNAME) values ('DE', 'Germany');
INSERT INTO OS_COUNTRY (COUNTRYCODE,COUNTRYNAME) values ('AT', 'Austria');
INSERT INTO OS_COUNTRY (COUNTRYCODE,COUNTRYNAME) values ('CH', 'Switzerland');

INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('BFRANK','BFRANK','Bernd','Frank',,'bernd.frank@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('DSTAUSS','DSTAUSS','Dirk','Stauss',,'dirk.stauss@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','AT');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('DJONES','DJONES','Dora','Jones',,'dora.jones@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('EBRANDT','EBRANDT','Ewald','Brandt',,'ewald.brandt@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','CH');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('GKLEIN','GKLEIN','Gerrit','Klein',,'gerrit.klein@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('GVOGT','GVOGT','Gitta','Vogt',,'gitta.vogt@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','CH');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('HSCHUMACHER','HSCHUMACHER','Helene','Schumacher',,'helene.schumacher@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('LSCHULTE','LSCHULTE','Lothur','Schulte',,'lothur.schulte@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','AT');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('LDERICHS','LDERICHS','Lutz','Derichs',,'lutz.derichs@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','AT');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('RPROTZ','RPROTZ','Rosemarie','Protz',,'rosemarie.protz@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');
INSERT INTO OS_ACCOUNT (USERID,USERNAME,FIRSTNAME,LASTNAME,PASSWORD,EMAIL,PROVISIONDATE,STATUS,COUNTRYCODE) values ('WSCHUBERT','WSCHUBERT','Wolf','Schubert',,'wolf.schubert@oracledemo.com',to_date('24-OCT-24','DD-MON-RR'),'ACTIVE','DE');

INSERT INTO OS_HOST (HOSTID,HOSTNAME) values ('host001','unixhost1');
INSERT INTO OS_HOST (HOSTID,HOSTNAME) values ('host002','unixhost2');
INSERT INTO OS_HOST (HOSTID,HOSTNAME) values ('host003','linuxhost1');
INSERT INTO OS_HOST (HOSTID,HOSTNAME) values ('host004','linuxhost2');

INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('BFRANK','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('BFRANK','host002');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('BFRANK','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('DJONES','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('DJONES','host002');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('DJONES','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('DSTAUSS','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('DSTAUSS','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('EBRANDT','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('EBRANDT','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('GKLEIN','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('GKLEIN','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('GKLEIN','host004');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('GVOGT','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('GVOGT','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('HSCHUMACHER','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('HSCHUMACHER','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('LDERICHS','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('LDERICHS','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('LSCHULTE','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('LSCHULTE','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('RPROTZ','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('RPROTZ','host003');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('RPROTZ','host004');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('WSCHUBERT','host001');
INSERT INTO OS_ACCOUNT_HOST (USERID,HOSTID) values ('WSCHUBERT','host003');
