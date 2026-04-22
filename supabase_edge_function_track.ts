// Edge Function: Tracking Pixel
// Registra quando um email é aberto
// Caminho: /functions/v1/track

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

serve(async (req) => {
  try {
    const url = new URL(req.url)
    const trackingId = url.searchParams.get('id')

    if (!trackingId) {
      return new Response('Missing tracking ID', { status: 400 })
    }

    // 1x1 transparent PNG pixel
    const pixel = Uint8Array.from([
      0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00,
      0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00,
      0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00, 0x0A, 0x49,
      0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
      0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00,
      0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])

    // Registrar abertura no Supabase (async, não bloqueia)
    fetch(`${SUPABASE_URL}/rest/v1/emails_enviados`, {
      method: 'PATCH',
      headers: {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tracking_id: trackingId,
        email_aberto: true,
        data_abertura: new Date().toISOString(),
        qtd_aberturas: 'coalesce(qtd_aberturas, 0) + 1'
      })
    }).catch(e => console.error('Erro ao registrar abertura:', e))

    // Retornar o pixel imediatamente
    return new Response(pixel, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
      },
    })
  } catch (error) {
    return new Response('Error', { status: 500 })
  }
})
