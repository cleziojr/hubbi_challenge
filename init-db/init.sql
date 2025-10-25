CREATE SCHEMA IF NOT EXISTS sch_precificacao;

CREATE TABLE IF NOT EXISTS sch_precificacao.product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    product_url VARCHAR(255),
    part_number VARCHAR(255),
    brand_name VARCHAR(100),
    category VARCHAR(100),
    price double precision,
    gross_weight double precision,
    width double precision,
    length double precision,
    warranty VARCHAR(10),
    material VARCHAR(100),
    photo_url VARCHAR(255),
    stock_quantity integer
);

GRANT ALL PRIVILEGES ON SCHEMA sch_precificacao TO hubbi;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sch_precificacao TO hubbi;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sch_precificacao TO hubbi;
