-- Check the PDB compatibility before plugging it in the target CDB

sqlplus / as sysdba
set serveroutput on
DECLARE
    compatible BOOLEAN := FALSE;
BEGIN
compatible := DBMS_PDB.CHECK_PLUG_COMPATIBILITY(
pdb_descr_file => '/home/oracle/PDB1.xml');
if compatible then
    DBMS_OUTPUT.PUT_LINE('Is pluggable PDB1.xml compatible? YES'); 
else 
    DBMS_OUTPUT.PUT_LINE('Is pluggable PDB1.xml compatible? NO');
end if;
END;
/