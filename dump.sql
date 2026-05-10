--
-- PostgreSQL database dump
--

\restrict R4qQoXwMlS7OMXudLfSK3s3g6o3XSrEJBkli0Rtl7dBCEWHhkkih4zmp0RYWe4Z

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: vpn_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO vpn_user;

--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: vpn_user
--

CREATE TABLE public.subscriptions (
    id bigint NOT NULL,
    tg_id bigint NOT NULL,
    start_at timestamp with time zone,
    end_at timestamp with time zone,
    subscription_link text,
    instructions text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    country text DEFAULT 'fi'::text NOT NULL,
    client_uuid text,
    sub_id text
);


ALTER TABLE public.subscriptions OWNER TO vpn_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: vpn_user
--

CREATE SEQUENCE public.subscriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptions_id_seq OWNER TO vpn_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vpn_user
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: vpn_user
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    tg_id bigint NOT NULL,
    username text,
    referrer_tg_id bigint,
    referral_balance integer DEFAULT 0 NOT NULL,
    balance integer DEFAULT 0 NOT NULL,
    first_payment_done boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    trial_used boolean DEFAULT false NOT NULL
);


ALTER TABLE public.users OWNER TO vpn_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: vpn_user
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO vpn_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vpn_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: vpn_user
--

COPY public.alembic_version (version_num) FROM stdin;
003_trial_and_manager
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: vpn_user
--

COPY public.subscriptions (id, tg_id, start_at, end_at, subscription_link, instructions, updated_at, country, client_uuid, sub_id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: vpn_user
--

COPY public.users (id, tg_id, username, referrer_tg_id, referral_balance, balance, first_payment_done, created_at, trial_used) FROM stdin;
61	2105111334	CANDDYBO1	5948443396	0	0	f	2026-02-10 18:12:14.308902+00	f
25	5948443396	szploxy	\N	75	0	f	2026-02-10 13:36:47.390643+00	f
66	969494698	slo1nk	5987926733	0	0	f	2026-02-11 04:03:30.953471+00	f
67	6098156904	Dev0n_hndrx	\N	0	0	f	2026-02-11 04:57:05.116561+00	f
11	1183899694	\N	\N	0	0	f	2026-02-03 13:12:37.220048+00	f
9	252033906	brhdshba	\N	0	0	f	2026-02-03 13:08:48.221712+00	f
270	326913987	\N	1008994432	0	0	f	2026-03-23 08:17:22.264568+00	f
69	641718270	rea1G	6098156904	0	0	f	2026-02-11 04:58:35.299637+00	f
8	5255574650	\N	\N	0	0	f	2026-02-03 13:03:42.504775+00	f
71	641636384	Razorb58	\N	0	0	f	2026-02-11 05:00:59.689307+00	f
77	1388134204	mupkiin	5948443396	0	0	f	2026-02-11 07:04:10.889111+00	f
79	1338957512	ChinaChingishanovich	\N	0	0	f	2026-02-11 09:50:34.283869+00	f
19	7369647098	lwsisasha	\N	0	0	f	2026-02-09 18:41:02.246945+00	f
33	5733257338	\N	\N	0	0	f	2026-02-10 14:20:28.052449+00	f
37	1227632265	VICTY666	\N	0	0	f	2026-02-10 14:30:21.011221+00	f
285	1629124928	knopa_skr	\N	0	0	f	2026-03-26 19:48:22.62376+00	f
170	1617518618	\N	\N	0	0	f	2026-02-17 06:31:00.711968+00	f
209	5675403580	\N	5229831062	0	0	f	2026-02-26 09:31:56.413123+00	f
173	1753480332	nenavijy666	\N	0	0	f	2026-02-18 14:16:21.974426+00	f
287	1780863102	gyfrfhb	\N	0	0	f	2026-03-27 03:52:42.442384+00	f
93	5037974893	bersiip	5948443396	0	0	f	2026-02-12 04:27:27.149346+00	f
277	5861751699	zopa0017	\N	0	0	f	2026-03-24 10:29:57.537822+00	f
230	6119303931	\N	\N	0	0	f	2026-03-02 03:30:19.208088+00	f
1	821740830	SkytNinja	\N	0	29250	f	2026-02-03 12:38:46.618015+00	f
64	5116462308	Iliketosleepppp	5948443396	0	0	f	2026-02-10 19:15:23.32016+00	f
298	1188959492	dddozy	\N	0	0	f	2026-03-28 16:26:44.840098+00	f
187	5247808192	bbbbbbbbph	\N	0	0	f	2026-02-21 12:31:25.836457+00	f
43	5987926733	GZD_779	5948443396	0	0	f	2026-02-10 14:51:44.40112+00	f
103	238916803	vasek_n	\N	0	0	f	2026-02-12 20:03:31.960501+00	f
244	5681400162	liza_srg_a	5948443396	0	0	f	2026-03-05 19:15:02.513773+00	f
40	1008994432	s1aveeek	\N	0	0	f	2026-02-10 14:42:29.689317+00	f
107	413073147	KorA_2728	\N	0	0	f	2026-02-13 15:41:13.713403+00	f
142	8598904248	nyxsupportvpn	\N	0	0	f	2026-02-14 09:02:37.745647+00	f
52	5229831062	shpscr	5948443396	0	0	t	2026-02-10 17:30:50.046182+00	f
151	1314105611	KosPar01	\N	0	0	f	2026-02-15 09:10:28.278117+00	f
154	979515364	\N	\N	0	0	f	2026-02-15 09:59:05.135287+00	f
150	6965462589	Kyke_7	5229831062	0	0	f	2026-02-14 19:02:18.643041+00	f
241	1990925580	wq1mss	\N	0	0	f	2026-03-02 12:50:33.473588+00	f
266	1459258114	I_II_II_II_I	\N	0	0	f	2026-03-17 17:51:44.170569+00	f
267	469120198	Fat_and_depressed	\N	0	0	f	2026-03-22 20:35:35.727552+00	f
\.


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vpn_user
--

SELECT pg_catalog.setval('public.subscriptions_id_seq', 29, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vpn_user
--

SELECT pg_catalog.setval('public.users_id_seq', 302, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_tg_id_key; Type: CONSTRAINT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_tg_id_key UNIQUE (tg_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_tg_id_key; Type: CONSTRAINT; Schema: public; Owner: vpn_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_tg_id_key UNIQUE (tg_id);


--
-- PostgreSQL database dump complete
--

\unrestrict R4qQoXwMlS7OMXudLfSK3s3g6o3XSrEJBkli0Rtl7dBCEWHhkkih4zmp0RYWe4Z

