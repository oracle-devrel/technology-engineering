create or replace type vc_arr_type
as table of varchar2(4000);
/

create or replace type json_arr_impl as object
(
  elements vc_arr_type,
  
  constructor function json_arr_impl(elem varchar2)
  return self as result,
  
  static function ODCIAggregateInitialize(sctx IN OUT json_arr_impl) 
                                          return number,
  
  member function ODCIAggregateIterate(self IN OUT json_arr_impl, 
                                       value IN varchar2) 
                                       return number,
  
  member function ODCIAggregateTerminate(self IN json_arr_impl, 
                                         returnValue OUT JSON, 
                                         flags IN number) 
                                         return number,
  
  member function ODCIAggregateMerge(self IN OUT json_arr_impl, 
                                     ctx2 IN json_arr_impl) 
                                     return number
);
/

create or replace type body json_arr_impl is 

  constructor function json_arr_impl(elem varchar2)
  return self as result
  is
  begin
    elements := vc_arr_type();
    if length(elem) <> 0 then
        elements.extend;
        elements(elements.count) := elem;
    end if;
    return;
  end;

  static function ODCIAggregateInitialize(sctx IN OUT json_arr_impl) 
                                          return number 
  is 
  begin
    sctx := json_arr_impl('');
    return ODCIConst.Success;
  end;

  member function ODCIAggregateIterate(self IN OUT json_arr_impl, 
                                       value IN varchar2) 
                                       return number 
  is
  begin
	elements.extend;
	elements(elements.count) := value;
    return ODCIConst.Success;
  end;

  member function ODCIAggregateTerminate(self IN json_arr_impl,
                                         returnValue OUT JSON, 
                                         flags IN number) 
                                         return number 
  is
  	jarr json_array_t := json_array_t();
  begin
    for i in 1..elements.count loop
        jarr.append(elements(i));
    end loop;
    returnValue := jarr.to_json();
    
    return ODCIConst.Success;
  end;

  member function ODCIAggregateMerge(self IN OUT json_arr_impl, 
                                     ctx2 IN json_arr_impl) 
                                     return number 
  is
  begin
    return ODCIConst.Success;
  end;
end;
/

CREATE OR REPLACE FUNCTION json_array_agg(input varchar2) RETURN json
PARALLEL_ENABLE AGGREGATE USING json_arr_impl;
/
