------------------------------------------------------
-- Simple Demo - Data Loading
------------------------------------------------------

-- Drop Table
drop table simple_demo_cohere;

-- Create Table
create table simple_demo_cohere (
  id   number primary key,
  text varchar2(128),
  text_v    vector
);

-- Truncate Table
truncate table simple_demo_cohere;

-- Insert Records into Table
insert into simple_demo_cohere values (1, 'San Francisco is in California.', null);
insert into simple_demo_cohere values (2, 'San Jose is in California.', null);
insert into simple_demo_cohere values (3, 'Los Angles is in California.', null);
insert into simple_demo_cohere values (4, 'Buffalo is in New York.', null);
insert into simple_demo_cohere values (5, 'Brooklyn is in New York.', null);
insert into simple_demo_cohere values (6, 'Queens is in New York.', null);
insert into simple_demo_cohere values (7, 'Harlem is in New York.', null);
insert into simple_demo_cohere values (8, 'The Bronx is in New York.', null);
insert into simple_demo_cohere values (9, 'Manhattan is in New York.', null);
insert into simple_demo_cohere values (10, 'Staten Island is in New York.', null);
insert into simple_demo_cohere values (11, 'Miami is in Florida.', null);
insert into simple_demo_cohere values (12, 'Tampa is in Florida.', null);
insert into simple_demo_cohere values (13, 'Orlando is in Florida.', null);
insert into simple_demo_cohere values (14, 'Dallas is in Texas.', null);
insert into simple_demo_cohere values (15, 'Huston is in Texas.', null);
insert into simple_demo_cohere values (16, 'Austin is in Texas.', null);
insert into simple_demo_cohere values (17, 'Phoenix is in Arizona.', null);
insert into simple_demo_cohere values (18, 'Las Vegas is in Nevada.', null);
insert into simple_demo_cohere values (19, 'Portland is in Oregon.', null);
insert into simple_demo_cohere values (20, 'New Orleans is in Louisiana.', null);
insert into simple_demo_cohere values (21, 'Atlanta is in Georgia.', null);
insert into simple_demo_cohere values (22, 'Chicago is in Illinois.', null);
insert into simple_demo_cohere values (23, 'Cleveland is in Ohio.', null);
insert into simple_demo_cohere values (24, 'Boston is in Massachusetts.', null);
insert into simple_demo_cohere values (25, 'Baltimore is in Maryland.', null);

insert into simple_demo_cohere values (100, 'Ferraris are often red.', null);
insert into simple_demo_cohere values (101, 'Teslas are electric.', null);
insert into simple_demo_cohere values (102, 'Mini coopers are small.', null);
insert into simple_demo_cohere values (103, 'Fiat 500 are small.', null);
insert into simple_demo_cohere values (104, 'Dodge Vipers are wide.', null);
insert into simple_demo_cohere values (105, 'Ford 150 are popular.', null);
insert into simple_demo_cohere values (106, 'Alfa Romeos are fun but unreliable.', null);
insert into simple_demo_cohere values (107, 'Volvos are safe.', null);
insert into simple_demo_cohere values (108, 'Toyotas are reliable.', null);
insert into simple_demo_cohere values (109, 'Hondas are reliable.', null);
insert into simple_demo_cohere values (110, 'Porsches are fast and reliable.', null);
insert into simple_demo_cohere values (111, 'Nissan GTR are great', null);
insert into simple_demo_cohere values (112, 'NISMO is awesome', null);

insert into simple_demo_cohere values (200, 'Bananas are yellow.', null);
insert into simple_demo_cohere values (201, 'Kiwis are green inside.', null);
insert into simple_demo_cohere values (202, 'Kiwis are brown on the outside.', null);
insert into simple_demo_cohere values (203, 'Kiwis are birds.', null);
insert into simple_demo_cohere values (204, 'Kiwis taste good.', null);
insert into simple_demo_cohere values (205, 'Ripe strawberries are red.', null);
insert into simple_demo_cohere values (206, 'Apples can be green, yellow or red.', null);
insert into simple_demo_cohere values (207, 'Ripe cherries are red.', null);
insert into simple_demo_cohere values (208, 'Pears can be green, yellow or brown.', null);
insert into simple_demo_cohere values (209, 'Oranges are orange.', null);
insert into simple_demo_cohere values (210, 'Peaches can be yellow, orange or red.', null);
insert into simple_demo_cohere values (211, 'Peaches can be fuzzy.', null);
insert into simple_demo_cohere values (212, 'Grapes can be green, red or purple.', null);
insert into simple_demo_cohere values (213, 'Watermelons are green on the outside.', null);
insert into simple_demo_cohere values (214, 'Watermelons are red on the outside.', null);
insert into simple_demo_cohere values (215, 'Blueberries are blue.', null);
insert into simple_demo_cohere values (216, 'Limes are green.', null);
insert into simple_demo_cohere values (217, 'Lemons are yellow.', null);
insert into simple_demo_cohere values (218, 'Ripe tomatoes are red.', null);
insert into simple_demo_cohere values (219, 'Unripe tomatoes are green.', null);
insert into simple_demo_cohere values (220, 'Ripe raspberries are red.', null);

insert into simple_demo_cohere values (300, 'Tigers have stripes.', null);
insert into simple_demo_cohere values (301, 'Lions are big.', null);
insert into simple_demo_cohere values (302, 'Mice are small.', null);
insert into simple_demo_cohere values (303, 'Cats do not care.', null);
insert into simple_demo_cohere values (304, 'Dogs are loyal.', null);
insert into simple_demo_cohere values (305, 'Bears are hairy.', null);
insert into simple_demo_cohere values (306, 'Pandas are black and white.', null);
insert into simple_demo_cohere values (307, 'Zebras are black and white.', null);
insert into simple_demo_cohere values (308, 'Penguins can be black and white.', null);
insert into simple_demo_cohere values (309, 'Puffins can be black and white.', null);
insert into simple_demo_cohere values (310, 'Giraffes have long necks.', null);
insert into simple_demo_cohere values (311, 'Elephants have trunks.', null);
insert into simple_demo_cohere values (312, 'Horses have four legs.', null);
insert into simple_demo_cohere values (313, 'Birds can fly.', null);
insert into simple_demo_cohere values (314, 'Birds lay eggs.', null);
insert into simple_demo_cohere values (315, 'Fish can swim.', null);
insert into simple_demo_cohere values (316, 'Sharks have lots of teeth.', null);
insert into simple_demo_cohere values (317, 'Flies can fly.', null);

insert into simple_demo_cohere values (400, 'Ibaraki is in Kanto.', null);
insert into simple_demo_cohere values (401, 'Tochigi is in Kanto.', null);
insert into simple_demo_cohere values (402, 'Gunma is in Kanto.', null);
insert into simple_demo_cohere values (403, 'Saitama is in Kanto.', null);
insert into simple_demo_cohere values (404, 'Chiba is in Kanto.', null);
insert into simple_demo_cohere values (405, 'Tokyo is in Kanto.', null);
insert into simple_demo_cohere values (406, 'Kanagawa is in Kanto.', null);

insert into simple_demo_cohere values (500, 'Eggs are egg shaped.', null);
insert into simple_demo_cohere values (501, 'Tokyo is in Japan.', null);
insert into simple_demo_cohere values (502, 'To be, or not to be, that is the question.', null);
insert into simple_demo_cohere values (503, '640K ought to be enough for anybody.', null);
insert into simple_demo_cohere values (504, 'Man overboard.', null);

-- Commit Changes
commit;

-- Count Records
select count(*) from simple_demo_cohere; -- 89 Records

-- Preview Data
select * from simple_demo_cohere order by id;


------------------------------------------------------
-- End of Script
------------------------------------------------------


