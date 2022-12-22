
drop table if exists product_cart;
drop table if exists product_in_order ;
drop table if exists product_rating ;
drop table if exists product;
drop table if exists category;
drop table if exists order_food cascade ;
drop table if exists user_db cascade;


create table user_db(
    user_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    user_login varchar(30)  NOT NULL,
    user_password varchar(255) NOT NULL,
    user_name varchar(200) NOT NULL,
    user_role varchar(40) DEFAULT 'User',
    phone_number INT NOT NULL
                );

create table order_food(
    order_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    status varchar(30) DEFAULT 'Processing',
    amount INT NOT NULL,
    order_date timestamp NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_db(user_id)
);

create table category
(
    category_id int PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    category_name varchar(60) NOT NULL
);

create table product(
    product_id int PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    category_id INT NOT NULL,
    manufacturer varchar(80) NOT NULL,
    country varchar(80) NOT NULL,
    price INT NOT NULL,
    product_name varchar(80),
    FOREIGN KEY(category_id) REFERENCES category(category_id)
);

create table product_rating(
    product_rate INT NOT NULL,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_db(user_id),
    FOREIGN KEY(product_id) REFERENCES product(product_id),
    PRIMARY KEY(user_id, product_id)
);

create table product_in_order(
    product_id INT NOT NULL,
    order_id INT NOT NULL,
    FOREIGN KEY(product_id) REFERENCES product(product_id),
    FOREIGN KEY(order_id) REFERENCES order_food(order_id),
    PRIMARY KEY(order_id, product_id)
);


create table product_cart(
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_db(user_id),
    FOREIGN KEY(product_id) REFERENCES product(product_id),
    PRIMARY KEY(user_id, product_id)
);


INSERT INTO category(category_name) VALUES ('Хлеб и выпечка'),
                                           ('Молочные'),
                                           ('Овощи и фрукты'),
                                           ('Мясо'),
                                           ('Рыба');

INSERT INTO product(category_id, manufacturer, country, price, product_name)
VALUES (1, 'Хлебокомбинат 1', 'Санкт-Петербург', 50, 'Булочка с корицей' ),
       (1, 'Хлебокомбинат 1', 'Санкт-Петербург', 70, 'Булочка с сосиской' ),
       (1, 'Хлебокомбинат 1', 'Санкт-Петербург', 60, 'Булочка с солью' ),
       (1, 'Хлебокомбинат 2', 'Волгоград', 60, 'Батон белого' ),
        (2, 'OAO Коровка', 'Москва', 100, 'Молоко 3.5% 1л.' ),
        (2, 'OAO Коровка', 'Москва', 110, 'Молоко 2.5% 1л.' ),
        (4, 'OAO Убить коровка', 'Москва', 300, 'Отборная телятина 1кг' );

