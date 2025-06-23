show databases;
use db_mediatek_menu;

show tables;

select * from med_sun;
select * from med_tpr;
select * from med_tpx;
select * from menu_items;

SELECT * FROM menu_items WHERE 餐廳名稱 = '味屋饕一番';
SELECT * FROM menu_items WHERE 菜牌編號 = 'ZZXCG-22RHVQOK';
SELECT * FROM med_tpx WHERE 英文名稱 = '';


SELECT * FROM med_sun 
WHERE DATE(建檔日期) = '2025-04-21';