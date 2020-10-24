drop table if exists users;
create table users(
    id integer primary key autoincrement,
    name string not null,
    email string not null,
    password string not null,
    salt string not null,
    photo_id string not null
);

drop table if exists user_photo;
create table user_photo(
    id integer primary key autoincrement,
    name string not null,
    org_photo string not null,
    thumbnail string not null,
    det_photo string not null
);