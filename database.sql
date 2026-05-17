--
-- PostgreSQL database dump
--

\restrict OyEW65ZVXP5LKiLL9daR3vcYRG00iwixX0HKqYr8K8EOT0H9YAUGjSezddNMWZ5

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2026-05-17 22:30:43

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 261 (class 1255 OID 25122)
-- Name: avg_dish_price(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.avg_dish_price() RETURNS numeric
    LANGUAGE sql
    AS $$
    SELECT AVG(price) FROM Dish;
$$;


ALTER FUNCTION public.avg_dish_price() OWNER TO postgres;

--
-- TOC entry 254 (class 1255 OID 25105)
-- Name: dish_cost(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.dish_cost(dish_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    total_cost NUMERIC(10,2);
    dish_markup NUMERIC(5,2);
BEGIN
    SELECT COALESCE(SUM(r.amount * i.purchase_price), 0)
    INTO total_cost
    FROM Recipe r
    JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
    WHERE r.id_dish = dish_id;
	
    SELECT markup INTO dish_markup
    FROM Dish
    WHERE id_dish = dish_id;

    UPDATE Dish
    SET calk_cost = total_cost,
        price = total_cost * (1 + dish_markup)
    WHERE id_dish = dish_id;
END;
$$;


ALTER FUNCTION public.dish_cost(dish_id integer) OWNER TO postgres;

--
-- TOC entry 262 (class 1255 OID 25123)
-- Name: dish_cost_markup_info(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.dish_cost_markup_info() RETURNS TABLE(dish_name character varying, cost numeric, markup_percent numeric)
    LANGUAGE sql
    AS $$
    SELECT name_dish, calk_cost, markup
    FROM Dish;
$$;


ALTER FUNCTION public.dish_cost_markup_info() OWNER TO postgres;

--
-- TOC entry 257 (class 1255 OID 25108)
-- Name: gen_check(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.gen_check(order_id integer) RETURNS TABLE(dish_name character varying, quantity integer, price_per_unit numeric, total_line numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT d.name_dish, oi.amount, d.price, oi.item_cost
    FROM Order_item oi
    JOIN Dish d ON oi.id_dish = d.id_dish
    WHERE oi.id_order = order_id;
END;
$$;


ALTER FUNCTION public.gen_check(order_id integer) OWNER TO postgres;

--
-- TOC entry 263 (class 1255 OID 25124)
-- Name: get_dish_name(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_dish_name(dish_id integer) RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    dish_name VARCHAR(64);
BEGIN
    SELECT name_dish INTO dish_name
    FROM Dish
    WHERE id_dish = dish_id;

    IF dish_name IS NULL THEN
        RAISE EXCEPTION 'Блюдо с ID % не найдено', dish_id;
    END IF;

    RETURN dish_name;
END;
$$;


ALTER FUNCTION public.get_dish_name(dish_id integer) OWNER TO postgres;

--
-- TOC entry 255 (class 1255 OID 25106)
-- Name: ingr_v_zakaze(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.ingr_v_zakaze(order_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    need_ingredient RECORD;
    total_needed numeric(10,3);
    current_stock numeric(10,3);
BEGIN
    FOR need_ingredient IN
        SELECT i.id_ingredient, SUM(oi.amount * r.amount) AS total_amount
        FROM Order_item oi
        JOIN Recipe r ON oi.id_dish = r.id_dish
        JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
        WHERE oi.id_order = order_id
        GROUP BY i.id_ingredient
    LOOP
        SELECT amount INTO current_stock
        FROM Ingredient
        WHERE id_ingredient = need_ingredient.id_ingredient;

        IF current_stock < need_ingredient.total_amount THEN
            RAISE EXCEPTION 'Недостаточно ингредиента %: требуется %, в наличии %',
                (SELECT name_i FROM Ingredient WHERE id_ingredient = need_ingredient.id_ingredient),
                need_ingredient.total_amount, current_stock;
        END IF;
    END LOOP;

    RETURN TRUE;
END;
$$;


ALTER FUNCTION public.ingr_v_zakaze(order_id integer) OWNER TO postgres;

--
-- TOC entry 260 (class 1255 OID 25115)
-- Name: izm_status_ingr(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.izm_status_ingr() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status = 'В приготовлении' AND OLD.status = 'Создан' THEN
        IF EXISTS (
            SELECT 1
            FROM Order_item oi
            WHERE oi.id_order = NEW.id_order
              AND srok_god(oi.id_dish)
        ) THEN
            RAISE EXCEPTION 'Невозможно начать приготовление: в заказе есть блюда с просроченными ингредиентами';
        END IF;
    END IF;
    IF NEW.status = 'Готов' AND OLD.status IN ('В приготовлении', 'Создан') THEN      
        PERFORM ingr_v_zakaze(NEW.id_order);   
        PERFORM spisanie_ingrid(NEW.id_order);
        NEW.close_datetime = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.izm_status_ingr() OWNER TO postgres;

--
-- TOC entry 241 (class 1255 OID 25113)
-- Name: izm_stoim_iznm_recept(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.izm_stoim_iznm_recept() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM dish_cost(NEW.id_dish);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.izm_stoim_iznm_recept() OWNER TO postgres;

--
-- TOC entry 240 (class 1255 OID 25111)
-- Name: sebe_stoim_zakup_change(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sebe_stoim_zakup_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM dish_cost(r.id_dish)
    FROM Recipe r
    WHERE r.id_ingredient = NEW.id_ingredient;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.sebe_stoim_zakup_change() OWNER TO postgres;

--
-- TOC entry 256 (class 1255 OID 25107)
-- Name: spisanie_ingrid(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.spisanie_ingrid(order_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    need_ingredient RECORD;
BEGIN
    FOR need_ingredient IN
        SELECT i.id_ingredient, SUM(oi.amount * r.amount) AS total_amount
        FROM Order_item oi
        JOIN Recipe r ON oi.id_dish = r.id_dish
        JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
        WHERE oi.id_order = order_id
        GROUP BY i.id_ingredient
    LOOP
        UPDATE Ingredient
        SET amount = amount - need_ingredient.total_amount
        WHERE id_ingredient = need_ingredient.id_ingredient;
    END LOOP;
END;
$$;


ALTER FUNCTION public.spisanie_ingrid(order_id integer) OWNER TO postgres;

--
-- TOC entry 259 (class 1255 OID 25110)
-- Name: srok_god(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.srok_god(dish_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM Recipe r
        JOIN Ingredient i ON r.id_ingredient = i.id_ingredient
        WHERE r.id_dish = dish_id
          AND i.expiration_date <= CURRENT_DATE
    );
END;
$$;


ALTER FUNCTION public.srok_god(dish_id integer) OWNER TO postgres;

--
-- TOC entry 258 (class 1255 OID 25109)
-- Name: top_blud(timestamp without time zone, timestamp without time zone, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.top_blud(period_start timestamp without time zone, period_end timestamp without time zone, top_n integer DEFAULT 5) RETURNS TABLE(dish_name character varying, total_sold integer, total_revenue numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT d.name_dish,
           SUM(oi.amount)::int,
           SUM(oi.item_cost)
    FROM Orderr o
    JOIN Order_item oi ON o.id_order = oi.id_order
    JOIN Dish d ON oi.id_dish = d.id_dish
    WHERE o.close_datetime BETWEEN period_start AND period_end
      AND o.status = 'Готов'
    GROUP BY d.id_dish, d.name_dish
    ORDER BY SUM(oi.item_cost) DESC
    LIMIT top_n;
END;
$$;


ALTER FUNCTION public.top_blud(period_start timestamp without time zone, period_end timestamp without time zone, top_n integer) OWNER TO postgres;

--
-- TOC entry 253 (class 1255 OID 25103)
-- Name: update_employee_hours_on_shift_end(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_employee_hours_on_shift_end() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    duration_hours INT;
BEGIN
    IF OLD.shift_end IS NULL AND NEW.shift_end IS NOT NULL THEN
        duration_hours := EXTRACT(EPOCH FROM (NEW.shift_end - NEW.shift_start)) / 3600;
        UPDATE Employee
        SET hours = COALESCE(hours, 0) + duration_hours
        WHERE id_employee IN (
            SELECT id_employee FROM Employee_Shift WHERE id_shift = NEW.id_shift
        );
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_employee_hours_on_shift_end() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 230 (class 1259 OID 25006)
-- Name: dish; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dish (
    id_dish integer NOT NULL,
    name_dish character varying(64) NOT NULL,
    ed_izmer character varying(16) NOT NULL,
    markup numeric(5,2),
    calk_cost numeric(10,2) DEFAULT 0 NOT NULL,
    price numeric(10,2) NOT NULL,
    CONSTRAINT chk_dish_markup CHECK ((markup > (0)::numeric))
);


ALTER TABLE public.dish OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 25005)
-- Name: dish_id_dish_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dish_id_dish_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dish_id_dish_seq OWNER TO postgres;

--
-- TOC entry 5067 (class 0 OID 0)
-- Dependencies: 229
-- Name: dish_id_dish_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dish_id_dish_seq OWNED BY public.dish.id_dish;


--
-- TOC entry 222 (class 1259 OID 24925)
-- Name: employee; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee (
    id_employee integer NOT NULL,
    ful_name character varying(120) NOT NULL,
    id_pos integer NOT NULL,
    date_of_birth date,
    contact_info character varying(32) NOT NULL,
    hours integer DEFAULT 0,
    status character varying(10) DEFAULT 'Активен'::character varying,
    login text NOT NULL,
    pass text NOT NULL,
    CONSTRAINT chk_employee_date_of_birth CHECK ((date_of_birth <= (CURRENT_DATE - '18 years'::interval))),
    CONSTRAINT chk_employee_hours CHECK ((hours >= 0)),
    CONSTRAINT chk_employee_status CHECK (((status)::text = ANY ((ARRAY['Активен'::character varying, 'Уволен'::character varying])::text[])))
);


ALTER TABLE public.employee OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 24924)
-- Name: employee_id_employee_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_id_employee_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_id_employee_seq OWNER TO postgres;

--
-- TOC entry 5068 (class 0 OID 0)
-- Dependencies: 221
-- Name: employee_id_employee_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employee_id_employee_seq OWNED BY public.employee.id_employee;


--
-- TOC entry 226 (class 1259 OID 24966)
-- Name: employee_shift; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employee_shift (
    id_es integer NOT NULL,
    id_employee integer NOT NULL,
    id_shift integer NOT NULL
);


ALTER TABLE public.employee_shift OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 24965)
-- Name: employee_shift_id_es_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employee_shift_id_es_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employee_shift_id_es_seq OWNER TO postgres;

--
-- TOC entry 5069 (class 0 OID 0)
-- Dependencies: 225
-- Name: employee_shift_id_es_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employee_shift_id_es_seq OWNED BY public.employee_shift.id_es;


--
-- TOC entry 228 (class 1259 OID 24986)
-- Name: ingredient; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ingredient (
    id_ingredient integer NOT NULL,
    name_i character varying(64) NOT NULL,
    ed_izmer character varying(16) NOT NULL,
    amount numeric(10,3) DEFAULT 0,
    delivery_date date NOT NULL,
    expiration_date date NOT NULL,
    purchase_price numeric(10,2) NOT NULL,
    CONSTRAINT chk_ingredient_amount CHECK ((amount >= (0)::numeric)),
    CONSTRAINT chk_ingredient_delivery_date CHECK ((delivery_date <= CURRENT_DATE)),
    CONSTRAINT chk_ingredient_expiration_date CHECK (((expiration_date > delivery_date) AND (expiration_date > CURRENT_DATE))),
    CONSTRAINT chk_ingredient_price CHECK ((purchase_price >= (0)::numeric))
);


ALTER TABLE public.ingredient OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 24985)
-- Name: ingredient_id_ingredient_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ingredient_id_ingredient_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ingredient_id_ingredient_seq OWNER TO postgres;

--
-- TOC entry 5070 (class 0 OID 0)
-- Dependencies: 227
-- Name: ingredient_id_ingredient_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ingredient_id_ingredient_seq OWNED BY public.ingredient.id_ingredient;


--
-- TOC entry 238 (class 1259 OID 25083)
-- Name: order_item; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.order_item (
    id_oi integer NOT NULL,
    id_order integer NOT NULL,
    id_dish integer NOT NULL,
    amount integer,
    item_cost numeric(10,2),
    CONSTRAINT chk_oi_amount CHECK ((amount > 0))
);


ALTER TABLE public.order_item OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 25082)
-- Name: order_item_id_oi_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.order_item_id_oi_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_item_id_oi_seq OWNER TO postgres;

--
-- TOC entry 5071 (class 0 OID 0)
-- Dependencies: 237
-- Name: order_item_id_oi_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.order_item_id_oi_seq OWNED BY public.order_item.id_oi;


--
-- TOC entry 236 (class 1259 OID 25054)
-- Name: orderr; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orderr (
    id_order integer NOT NULL,
    id_table integer NOT NULL,
    id_waiter integer NOT NULL,
    id_cook integer,
    status character varying(20) DEFAULT 'Создан'::character varying,
    total_cost numeric(10,2) DEFAULT 0,
    close_datetime timestamp without time zone,
    order_created timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_order_status CHECK (((status)::text = ANY ((ARRAY['Создан'::character varying, 'В приготовлении'::character varying, 'Готов'::character varying])::text[])))
);


ALTER TABLE public.orderr OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 25053)
-- Name: orderr_id_order_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.orderr_id_order_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orderr_id_order_seq OWNER TO postgres;

--
-- TOC entry 5072 (class 0 OID 0)
-- Dependencies: 235
-- Name: orderr_id_order_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.orderr_id_order_seq OWNED BY public.orderr.id_order;


--
-- TOC entry 220 (class 1259 OID 24912)
-- Name: post; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.post (
    id_pos integer NOT NULL,
    title character varying(64) NOT NULL,
    salary numeric(10,2) NOT NULL,
    CONSTRAINT chk_post_salary CHECK ((salary >= (0)::numeric))
);


ALTER TABLE public.post OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 24911)
-- Name: post_id_pos_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.post_id_pos_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.post_id_pos_seq OWNER TO postgres;

--
-- TOC entry 5073 (class 0 OID 0)
-- Dependencies: 219
-- Name: post_id_pos_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.post_id_pos_seq OWNED BY public.post.id_pos;


--
-- TOC entry 232 (class 1259 OID 25022)
-- Name: recipe; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recipe (
    id_recipe integer NOT NULL,
    id_dish integer NOT NULL,
    id_ingredient integer NOT NULL,
    amount numeric(10,3),
    CONSTRAINT chk_recipe_amount CHECK ((amount > (0)::numeric))
);


ALTER TABLE public.recipe OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 25021)
-- Name: recipe_id_recipe_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.recipe_id_recipe_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recipe_id_recipe_seq OWNER TO postgres;

--
-- TOC entry 5074 (class 0 OID 0)
-- Dependencies: 231
-- Name: recipe_id_recipe_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.recipe_id_recipe_seq OWNED BY public.recipe.id_recipe;


--
-- TOC entry 239 (class 1259 OID 25117)
-- Name: recipe_management; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.recipe_management AS
 SELECT r.id_recipe,
    d.name_dish,
    d.price,
    i.name_i AS ingredient_name,
    r.amount AS required_amount,
    i.amount AS current_stock,
    i.expiration_date,
    (i.amount >= r.amount) AS has_sufficient_stock
   FROM ((public.recipe r
     JOIN public.dish d ON ((r.id_dish = d.id_dish)))
     JOIN public.ingredient i ON ((r.id_ingredient = i.id_ingredient)))
  WHERE (i.expiration_date > CURRENT_DATE);


ALTER VIEW public.recipe_management OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 24954)
-- Name: shift; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift (
    id_shift integer NOT NULL,
    shift_date date NOT NULL,
    shift_start timestamp without time zone NOT NULL,
    shift_end timestamp without time zone NOT NULL,
    CONSTRAINT chk_shift_time CHECK ((shift_end > shift_start))
);


ALTER TABLE public.shift OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 24953)
-- Name: shift_id_shift_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_id_shift_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_id_shift_seq OWNER TO postgres;

--
-- TOC entry 5075 (class 0 OID 0)
-- Dependencies: 223
-- Name: shift_id_shift_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_id_shift_seq OWNED BY public.shift.id_shift;


--
-- TOC entry 234 (class 1259 OID 25043)
-- Name: tableinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tableinfo (
    id_table integer NOT NULL,
    table_number integer,
    seats integer,
    reserved boolean DEFAULT false,
    reservation_time timestamp without time zone,
    CONSTRAINT chk_table_seats CHECK ((seats > 0)),
    CONSTRAINT chk_table_time CHECK ((reservation_time >= CURRENT_TIMESTAMP))
);


ALTER TABLE public.tableinfo OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 25042)
-- Name: tableinfo_id_table_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tableinfo_id_table_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tableinfo_id_table_seq OWNER TO postgres;

--
-- TOC entry 5076 (class 0 OID 0)
-- Dependencies: 233
-- Name: tableinfo_id_table_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tableinfo_id_table_seq OWNED BY public.tableinfo.id_table;


--
-- TOC entry 4825 (class 2604 OID 25009)
-- Name: dish id_dish; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dish ALTER COLUMN id_dish SET DEFAULT nextval('public.dish_id_dish_seq'::regclass);


--
-- TOC entry 4818 (class 2604 OID 24928)
-- Name: employee id_employee; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee ALTER COLUMN id_employee SET DEFAULT nextval('public.employee_id_employee_seq'::regclass);


--
-- TOC entry 4822 (class 2604 OID 24969)
-- Name: employee_shift id_es; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_shift ALTER COLUMN id_es SET DEFAULT nextval('public.employee_shift_id_es_seq'::regclass);


--
-- TOC entry 4823 (class 2604 OID 24989)
-- Name: ingredient id_ingredient; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredient ALTER COLUMN id_ingredient SET DEFAULT nextval('public.ingredient_id_ingredient_seq'::regclass);


--
-- TOC entry 4834 (class 2604 OID 25086)
-- Name: order_item id_oi; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_item ALTER COLUMN id_oi SET DEFAULT nextval('public.order_item_id_oi_seq'::regclass);


--
-- TOC entry 4830 (class 2604 OID 25057)
-- Name: orderr id_order; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orderr ALTER COLUMN id_order SET DEFAULT nextval('public.orderr_id_order_seq'::regclass);


--
-- TOC entry 4817 (class 2604 OID 24915)
-- Name: post id_pos; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post ALTER COLUMN id_pos SET DEFAULT nextval('public.post_id_pos_seq'::regclass);


--
-- TOC entry 4827 (class 2604 OID 25025)
-- Name: recipe id_recipe; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recipe ALTER COLUMN id_recipe SET DEFAULT nextval('public.recipe_id_recipe_seq'::regclass);


--
-- TOC entry 4821 (class 2604 OID 24957)
-- Name: shift id_shift; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift ALTER COLUMN id_shift SET DEFAULT nextval('public.shift_id_shift_seq'::regclass);


--
-- TOC entry 4828 (class 2604 OID 25046)
-- Name: tableinfo id_table; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tableinfo ALTER COLUMN id_table SET DEFAULT nextval('public.tableinfo_id_table_seq'::regclass);


--
-- TOC entry 5053 (class 0 OID 25006)
-- Dependencies: 230
-- Data for Name: dish; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dish (id_dish, name_dish, ed_izmer, markup, calk_cost, price) FROM stdin;
1	Борщ	порция	2.50	201.50	705.25
2	Паста Карбонара	порция	2.80	121.60	462.08
3	Стейк Рибай	порция	3.00	210.00	840.00
4	Салат Цезарь	порция	2.60	78.40	282.24
5	Куриные наггетсы	порция	2.40	87.50	297.50
6	Оливье	порция	2.30	6.80	22.44
7	Чизбургер	шт	2.70	70.00	259.00
8	Пицца Маргарита	шт	2.90	15.00	58.50
9	Капучино	стакан	3.50	14.00	63.00
10	Тирамису	порция	3.20	83.50	350.70
\.


--
-- TOC entry 5045 (class 0 OID 24925)
-- Dependencies: 222
-- Data for Name: employee; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee (id_employee, ful_name, id_pos, date_of_birth, contact_info, hours, status, login, pass) FROM stdin;
1	Иванов Иван Иванович	1	1990-03-15	+79001111111	160	Активен	+79001111111	123
2	Петров Пётр Петрович	2	1985-07-22	+79002222222	150	Активен	+79002222222	123
3	Сидорова Анна Сергеевна	3	2000-12-01	+79003333333	140	Активен	+79003333333	123
4	Кузнецов Дмитрий Викторович	4	1978-11-05	+79004444444	0	Уволен	+79004444444	123
5	Морозова Елена Андреевна	5	1995-02-28	+79005555555	170	Активен	+79005555555	123
6	Соколов Алексей Николаевич	6	1988-09-10	+79006666666	165	Активен	+79006666666	123
7	Волкова Мария Игоревна	2	2001-05-30	+79007777777	145	Активен	+79007777777	123
8	Лебедев Сергей Павлович	7	1982-04-14	+79008888888	180	Активен	+79008888888	123
9	Новикова Ольга Владимировна	8	1993-08-19	+79009999999	155	Активен	+79009999999	123
10	Григорьев Артём Олегович	2	2002-01-15	+79010000000	\N	Активен	+79010000000	123
11	Администратор	8	1990-01-01	+79000000001	0	Активен	admin	admin
12	Менеджер	5	1988-05-15	+79000000002	0	Активен	manager	manager
13	Шеф-повар	7	1985-11-20	+79000000003	0	Активен	chef	chef
14	Повар	1	1992-03-10	+79000000004	0	Активен	cook	cook
15	Официант 	2	1998-02-28	+79000000007	0	Активен	waiter	waiter
\.


--
-- TOC entry 5049 (class 0 OID 24966)
-- Dependencies: 226
-- Data for Name: employee_shift; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.employee_shift (id_es, id_employee, id_shift) FROM stdin;
1	1	1
2	2	1
3	2	2
4	3	1
5	4	1
6	5	3
7	6	3
8	7	4
9	8	5
10	9	6
11	10	7
12	1	3
13	2	5
14	3	7
\.


--
-- TOC entry 5051 (class 0 OID 24986)
-- Dependencies: 228
-- Data for Name: ingredient; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ingredient (id_ingredient, name_i, ed_izmer, amount, delivery_date, expiration_date, purchase_price) FROM stdin;
1	Куриное филе	кг	50.000	2026-05-12	2026-07-16	350.00
2	Говядина	кг	30.000	2026-05-14	2026-08-15	600.00
3	Картофель	кг	100.000	2026-05-10	2026-07-01	40.00
6	Томаты	кг	25.000	2026-05-16	2026-05-29	120.00
7	Лук репчатый	кг	40.000	2026-05-11	2026-08-05	30.00
8	Сливки 20%	л	15.000	2026-05-16	2026-05-24	100.00
9	Мука пшеничная	кг	60.000	2026-05-07	2026-09-14	50.00
10	Яйца куриные	шт	300.000	2026-05-17	2026-06-06	0.80
4	Молоко	л	19.950	2026-05-15	2026-05-25	70.00
5	Сыр моцарелла	кг	9.900	2026-05-13	2026-07-06	800.00
\.


--
-- TOC entry 5061 (class 0 OID 25083)
-- Dependencies: 238
-- Data for Name: order_item; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.order_item (id_oi, id_order, id_dish, amount, item_cost) FROM stdin;
1	1	1	1	300.00
2	1	9	2	280.00
3	2	2	1	420.00
4	2	4	2	520.00
5	5	1	1	300.00
6	6	2	1	420.00
7	6	7	1	243.00
8	6	9	1	140.00
9	8	2	1	420.00
10	10	9	1	140.00
11	3	3	1	1500.00
12	4	5	1	192.00
13	7	10	1	352.00
14	9	10	1	352.00
\.


--
-- TOC entry 5059 (class 0 OID 25054)
-- Dependencies: 236
-- Data for Name: orderr; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.orderr (id_order, id_table, id_waiter, id_cook, status, total_cost, close_datetime, order_created) FROM stdin;
1	1	2	1	Готов	460.00	2025-12-01 20:30:00	2025-12-01 20:00:00
2	2	7	1	Готов	682.00	2025-12-01 21:15:00	2025-12-01 20:45:00
3	3	2	6	В приготовлении	1500.00	\N	2025-01-10 19:05:00
4	4	7	6	Создан	0.00	\N	2025-01-05 19:55:00
5	5	2	1	Готов	300.00	2025-12-02 13:10:00	2025-12-02 13:00:00
6	6	7	8	Готов	763.00	2025-12-03 20:45:00	2025-12-03 20:15:00
7	7	2	1	Создан	0.00	\N	2025-01-15 18:35:00
8	8	7	6	Готов	420.00	2025-12-04 21:00:00	2025-12-04 20:30:00
10	10	7	1	Готов	140.00	2025-12-06 08:20:00	2025-12-06 07:00:00
11	10	7	1	Готов	140.00	2025-12-07 04:20:00	2025-12-07 05:00:00
12	10	7	1	Готов	140.00	2025-12-08 21:20:00	2025-12-08 22:00:00
13	10	7	1	Готов	140.00	2025-12-09 02:20:00	2025-12-09 03:00:00
14	10	7	1	Готов	140.00	2025-12-05 14:20:00	2025-12-05 14:00:00
9	9	2	8	Готов	352.00	2026-05-17 22:27:16.481275	2025-01-20 19:35:00
\.


--
-- TOC entry 5043 (class 0 OID 24912)
-- Dependencies: 220
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.post (id_pos, title, salary) FROM stdin;
1	Повар	65000.00
2	Официант	45000.00
3	Бариста	48000.00
4	Уборщик	35000.00
5	Менеджер зала	70000.00
6	Су-шеф	85000.00
7	Шеф-повар	120000.00
8	Администратор	55000.00
9	Бармен	50000.00
10	Помощник повара	40000.00
\.


--
-- TOC entry 5055 (class 0 OID 25022)
-- Dependencies: 232
-- Data for Name: recipe; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.recipe (id_recipe, id_dish, id_ingredient, amount) FROM stdin;
1	1	2	0.300
2	1	3	0.200
3	1	6	0.100
4	1	7	0.050
5	2	10	2.000
6	2	5	0.150
7	3	2	0.350
8	4	6	0.120
9	4	5	0.080
10	5	1	0.250
11	6	3	0.150
12	6	10	1.000
13	7	1	0.200
14	8	9	0.300
15	9	4	0.200
16	10	5	0.100
17	10	4	0.050
\.


--
-- TOC entry 5047 (class 0 OID 24954)
-- Dependencies: 224
-- Data for Name: shift; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.shift (id_shift, shift_date, shift_start, shift_end) FROM stdin;
1	2025-12-01	2025-12-01 08:00:00	2025-12-01 16:00:00
2	2025-12-01	2025-12-01 16:00:00	2025-12-01 23:59:59
3	2025-12-02	2025-12-02 08:00:00	2025-12-02 16:00:00
4	2025-12-02	2025-12-02 16:00:00	2025-12-02 23:59:59
5	2025-12-03	2025-12-03 08:00:00	2025-12-03 16:00:00
6	2025-12-04	2025-12-04 08:00:00	2025-12-04 16:00:00
7	2025-12-05	2025-12-05 08:00:00	2025-12-05 16:00:00
8	2025-12-06	2025-12-06 08:00:00	2025-12-06 16:00:00
9	2025-12-07	2025-12-07 08:00:00	2025-12-07 16:00:00
10	2025-12-08	2025-12-08 08:00:00	2025-12-08 16:00:00
\.


--
-- TOC entry 5057 (class 0 OID 25043)
-- Dependencies: 234
-- Data for Name: tableinfo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tableinfo (id_table, table_number, seats, reserved, reservation_time) FROM stdin;
1	1	2	f	\N
2	2	4	f	\N
3	3	6	t	2026-07-10 19:00:00
4	4	2	t	2026-06-20 20:00:00
5	5	8	f	\N
6	6	4	f	\N
7	7	2	t	2026-07-15 18:30:00
8	8	6	f	\N
9	9	4	t	2026-07-20 19:30:00
10	10	2	f	\N
\.


--
-- TOC entry 5077 (class 0 OID 0)
-- Dependencies: 229
-- Name: dish_id_dish_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dish_id_dish_seq', 10, true);


--
-- TOC entry 5078 (class 0 OID 0)
-- Dependencies: 221
-- Name: employee_id_employee_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_id_employee_seq', 15, true);


--
-- TOC entry 5079 (class 0 OID 0)
-- Dependencies: 225
-- Name: employee_shift_id_es_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.employee_shift_id_es_seq', 14, true);


--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 227
-- Name: ingredient_id_ingredient_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ingredient_id_ingredient_seq', 10, true);


--
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 237
-- Name: order_item_id_oi_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.order_item_id_oi_seq', 14, true);


--
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 235
-- Name: orderr_id_order_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.orderr_id_order_seq', 14, true);


--
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 219
-- Name: post_id_pos_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.post_id_pos_seq', 10, true);


--
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 231
-- Name: recipe_id_recipe_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.recipe_id_recipe_seq', 17, true);


--
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 223
-- Name: shift_id_shift_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.shift_id_shift_seq', 10, true);


--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 233
-- Name: tableinfo_id_table_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tableinfo_id_table_seq', 10, true);


--
-- TOC entry 4869 (class 2606 OID 25020)
-- Name: dish dish_name_dish_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dish
    ADD CONSTRAINT dish_name_dish_key UNIQUE (name_dish);


--
-- TOC entry 4871 (class 2606 OID 25018)
-- Name: dish dishpk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dish
    ADD CONSTRAINT dishpk PRIMARY KEY (id_dish);


--
-- TOC entry 4855 (class 2606 OID 24945)
-- Name: employee employee_contact_info_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_contact_info_key UNIQUE (contact_info);


--
-- TOC entry 4857 (class 2606 OID 24947)
-- Name: employee employee_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_login_key UNIQUE (login);


--
-- TOC entry 4859 (class 2606 OID 24943)
-- Name: employee employeepk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employeepk PRIMARY KEY (id_employee);


--
-- TOC entry 4863 (class 2606 OID 24974)
-- Name: employee_shift espk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_shift
    ADD CONSTRAINT espk PRIMARY KEY (id_es);


--
-- TOC entry 4865 (class 2606 OID 25004)
-- Name: ingredient ingredient_name_i_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredient
    ADD CONSTRAINT ingredient_name_i_key UNIQUE (name_i);


--
-- TOC entry 4867 (class 2606 OID 25002)
-- Name: ingredient ingredientpk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingredient
    ADD CONSTRAINT ingredientpk PRIMARY KEY (id_ingredient);


--
-- TOC entry 4879 (class 2606 OID 25092)
-- Name: order_item oipk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT oipk PRIMARY KEY (id_oi);


--
-- TOC entry 4877 (class 2606 OID 25066)
-- Name: orderr orderpk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orderr
    ADD CONSTRAINT orderpk PRIMARY KEY (id_order);


--
-- TOC entry 4851 (class 2606 OID 24923)
-- Name: post post_title_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_title_key UNIQUE (title);


--
-- TOC entry 4853 (class 2606 OID 24921)
-- Name: post postpk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT postpk PRIMARY KEY (id_pos);


--
-- TOC entry 4873 (class 2606 OID 25031)
-- Name: recipe recipepk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recipe
    ADD CONSTRAINT recipepk PRIMARY KEY (id_recipe);


--
-- TOC entry 4861 (class 2606 OID 24964)
-- Name: shift shiftpk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shiftpk PRIMARY KEY (id_shift);


--
-- TOC entry 4875 (class 2606 OID 25052)
-- Name: tableinfo tablepk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tableinfo
    ADD CONSTRAINT tablepk PRIMARY KEY (id_table);


--
-- TOC entry 4892 (class 2620 OID 25114)
-- Name: recipe trig_izm_stoim_iznm_recept; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trig_izm_stoim_iznm_recept AFTER INSERT OR DELETE OR UPDATE ON public.recipe FOR EACH ROW EXECUTE FUNCTION public.izm_stoim_iznm_recept();


--
-- TOC entry 4893 (class 2620 OID 25116)
-- Name: orderr trig_order_status; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trig_order_status BEFORE UPDATE OF status ON public.orderr FOR EACH ROW EXECUTE FUNCTION public.izm_status_ingr();


--
-- TOC entry 4891 (class 2620 OID 25112)
-- Name: ingredient trig_sebe_stoim_zakup_change; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trig_sebe_stoim_zakup_change AFTER UPDATE OF purchase_price ON public.ingredient FOR EACH ROW EXECUTE FUNCTION public.sebe_stoim_zakup_change();


--
-- TOC entry 4890 (class 2620 OID 25104)
-- Name: shift trig_update_employee_hours; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trig_update_employee_hours BEFORE UPDATE OF shift_end ON public.shift FOR EACH ROW EXECUTE FUNCTION public.update_employee_hours_on_shift_end();


--
-- TOC entry 4880 (class 2606 OID 24948)
-- Name: employee employeefk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employeefk FOREIGN KEY (id_pos) REFERENCES public.post(id_pos) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4881 (class 2606 OID 24975)
-- Name: employee_shift esfk1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_shift
    ADD CONSTRAINT esfk1 FOREIGN KEY (id_employee) REFERENCES public.employee(id_employee) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4882 (class 2606 OID 24980)
-- Name: employee_shift esfk2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employee_shift
    ADD CONSTRAINT esfk2 FOREIGN KEY (id_shift) REFERENCES public.shift(id_shift) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4888 (class 2606 OID 25093)
-- Name: order_item oifk1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT oifk1 FOREIGN KEY (id_order) REFERENCES public.orderr(id_order) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4889 (class 2606 OID 25098)
-- Name: order_item oifk2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT oifk2 FOREIGN KEY (id_dish) REFERENCES public.dish(id_dish) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4885 (class 2606 OID 25067)
-- Name: orderr orderfk1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orderr
    ADD CONSTRAINT orderfk1 FOREIGN KEY (id_table) REFERENCES public.tableinfo(id_table) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4886 (class 2606 OID 25072)
-- Name: orderr orderfk2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orderr
    ADD CONSTRAINT orderfk2 FOREIGN KEY (id_waiter) REFERENCES public.employee(id_employee) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4887 (class 2606 OID 25077)
-- Name: orderr orderfk3; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orderr
    ADD CONSTRAINT orderfk3 FOREIGN KEY (id_cook) REFERENCES public.employee(id_employee) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- TOC entry 4883 (class 2606 OID 25032)
-- Name: recipe recipefk1; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recipe
    ADD CONSTRAINT recipefk1 FOREIGN KEY (id_dish) REFERENCES public.dish(id_dish) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 4884 (class 2606 OID 25037)
-- Name: recipe recipefk2; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recipe
    ADD CONSTRAINT recipefk2 FOREIGN KEY (id_ingredient) REFERENCES public.ingredient(id_ingredient) ON UPDATE CASCADE ON DELETE RESTRICT;


-- Completed on 2026-05-17 22:30:44

--
-- PostgreSQL database dump complete
--

\unrestrict OyEW65ZVXP5LKiLL9daR3vcYRG00iwixX0HKqYr8K8EOT0H9YAUGjSezddNMWZ5

