create or replace function partial_value(data JSON) return number
deterministic
is
begin
	if json_value(data, '$.salary') < 8000 then
		return json_value(data, '$.salary' returning number error on error);
	end if;
	return null;
end;
/
