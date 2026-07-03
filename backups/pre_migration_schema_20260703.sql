--
-- PostgreSQL database dump
--

\restrict VuqtMXtxeG6rczGdGyxglmMbcT7g3OGO0wgXKNbhVIAEyOKigCHrxbZpwcOIObV

-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.0

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: lead_interactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lead_interactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    lead_id uuid NOT NULL,
    tipo text NOT NULL,
    canal text DEFAULT ''::text,
    mensagem text DEFAULT ''::text,
    observacao text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT lead_interactions_tipo_check CHECK ((tipo = ANY (ARRAY['importacao'::text, 'primeira_abordagem'::text, 'primeira_abordagem_manual_antiga'::text, 'follow_up'::text, 'resposta_cliente'::text, 'proposta_enviada'::text, 'convertido'::text, 'perdido'::text])))
);


ALTER TABLE public.lead_interactions OWNER TO postgres;

--
-- Name: leads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.leads (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nome text DEFAULT ''::text NOT NULL,
    telefone text DEFAULT ''::text,
    whatsapp text DEFAULT ''::text,
    telefone_normalizado text,
    instagram text DEFAULT ''::text,
    email text DEFAULT ''::text,
    categoria text DEFAULT ''::text,
    nicho text DEFAULT ''::text,
    cidade text DEFAULT ''::text,
    bairro text DEFAULT ''::text,
    endereco text DEFAULT ''::text,
    tem_site boolean DEFAULT false,
    url_site text DEFAULT ''::text,
    avaliacao numeric(3,1) DEFAULT 0,
    num_avaliacoes integer DEFAULT 0,
    score integer DEFAULT 0,
    prioridade text DEFAULT ''::text,
    oferta_sugerida text DEFAULT ''::text,
    mensagem_whatsapp text DEFAULT ''::text,
    link_whatsapp text DEFAULT ''::text,
    status text DEFAULT 'novo'::text NOT NULL,
    origem text DEFAULT ''::text,
    ultimo_contato_em timestamp with time zone,
    proximo_followup_em timestamp with time zone,
    observacoes text DEFAULT ''::text,
    resposta_cliente text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    produto text DEFAULT 'landing'::text,
    grupo text DEFAULT ''::text,
    subnicho text DEFAULT ''::text,
    faz_assistencia text DEFAULT ''::text,
    score_avgestao integer DEFAULT 0,
    motivos_score text DEFAULT ''::text,
    nome_curto text DEFAULT ''::text,
    uf text DEFAULT ''::text,
    estado text DEFAULT ''::text,
    regiao text DEFAULT ''::text,
    source_query text DEFAULT ''::text,
    source_scope text DEFAULT ''::text,
    run_id text DEFAULT ''::text,
    captured_at timestamp with time zone,
    place_id text DEFAULT ''::text,
    maps_url text DEFAULT ''::text,
    CONSTRAINT leads_status_check CHECK ((status = ANY (ARRAY['novo'::text, 'pronto_para_enviar'::text, 'abordado'::text, 'respondeu'::text, 'follow_up'::text, 'interessado'::text, 'convertido'::text, 'perdido'::text])))
);


ALTER TABLE public.leads OWNER TO postgres;

--
-- Name: lead_interactions lead_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_interactions
    ADD CONSTRAINT lead_interactions_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: leads leads_telefone_normalizado_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_telefone_normalizado_key UNIQUE (telefone_normalizado);


--
-- Name: idx_interactions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interactions_created_at ON public.lead_interactions USING btree (created_at);


--
-- Name: idx_interactions_lead_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interactions_lead_id ON public.lead_interactions USING btree (lead_id);


--
-- Name: idx_interactions_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interactions_tipo ON public.lead_interactions USING btree (tipo);


--
-- Name: idx_leads_categoria; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_categoria ON public.leads USING btree (categoria);


--
-- Name: idx_leads_cidade; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_cidade ON public.leads USING btree (cidade);


--
-- Name: idx_leads_grupo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_grupo ON public.leads USING btree (grupo);


--
-- Name: idx_leads_nicho; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_nicho ON public.leads USING btree (nicho);


--
-- Name: idx_leads_origem; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_origem ON public.leads USING btree (origem);


--
-- Name: idx_leads_place_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_place_id ON public.leads USING btree (place_id);


--
-- Name: idx_leads_produto; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_produto ON public.leads USING btree (produto);


--
-- Name: idx_leads_proximo_followup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_proximo_followup ON public.leads USING btree (proximo_followup_em);


--
-- Name: idx_leads_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_run_id ON public.leads USING btree (run_id);


--
-- Name: idx_leads_score; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_score ON public.leads USING btree (score DESC);


--
-- Name: idx_leads_score_avgestao; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_score_avgestao ON public.leads USING btree (score_avgestao DESC);


--
-- Name: idx_leads_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_status ON public.leads USING btree (status);


--
-- Name: idx_leads_subnicho; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_subnicho ON public.leads USING btree (subnicho);


--
-- Name: idx_leads_uf; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_leads_uf ON public.leads USING btree (uf);


--
-- Name: leads set_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.leads FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: lead_interactions lead_interactions_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_interactions
    ADD CONSTRAINT lead_interactions_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;


--
-- Name: lead_interactions Interactions: insert para anon; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Interactions: insert para anon" ON public.lead_interactions FOR INSERT TO anon WITH CHECK (true);


--
-- Name: lead_interactions Interactions: select para anon; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Interactions: select para anon" ON public.lead_interactions FOR SELECT TO anon USING (true);


--
-- Name: leads Leads: insert para anon; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Leads: insert para anon" ON public.leads FOR INSERT TO anon WITH CHECK (true);


--
-- Name: leads Leads: select para anon; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Leads: select para anon" ON public.leads FOR SELECT TO anon USING (true);


--
-- Name: leads Leads: update para anon; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Leads: update para anon" ON public.leads FOR UPDATE TO anon USING (true) WITH CHECK (true);


--
-- Name: lead_interactions; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.lead_interactions ENABLE ROW LEVEL SECURITY;

--
-- Name: leads; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

--
-- Name: TABLE lead_interactions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.lead_interactions TO anon;
GRANT ALL ON TABLE public.lead_interactions TO authenticated;
GRANT ALL ON TABLE public.lead_interactions TO service_role;


--
-- Name: TABLE leads; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.leads TO anon;
GRANT ALL ON TABLE public.leads TO authenticated;
GRANT ALL ON TABLE public.leads TO service_role;


--
-- PostgreSQL database dump complete
--

\unrestrict VuqtMXtxeG6rczGdGyxglmMbcT7g3OGO0wgXKNbhVIAEyOKigCHrxbZpwcOIObV

