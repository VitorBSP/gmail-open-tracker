import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const transparentPixel = Uint8Array.from(
  atob("R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="),
  (character) => character.charCodeAt(0),
);

const tokenPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

Deno.serve(async (request: Request): Promise<Response> => {
  const url = new URL(request.url);
  const token = url.searchParams.get("id");

  if (
    request.method !== "GET" ||
    !url.pathname.endsWith("/email-open-pixel") ||
    !token ||
    !tokenPattern.test(token)
  ) {
    return new Response("Not Found", { status: 404 });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (supabaseUrl && serviceRoleKey) {
    try {
      const authorizationHeaders = {
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
      };

      const messageResponse = await fetch(
        `${supabaseUrl}/rest/v1/caucao_email_tracker_messages?token=eq.${encodeURIComponent(token)}&select=token&limit=1`,
        { headers: authorizationHeaders },
      );
      const matchingMessages = messageResponse.ok
        ? await messageResponse.json()
        : [];

      if (matchingMessages.length === 1) {
        const eventResponse = await fetch(
          `${supabaseUrl}/rest/v1/caucao_email_tracker_requests`,
          {
            method: "POST",
            headers: {
              ...authorizationHeaders,
              "Content-Type": "application/json",
              Prefer: "return=minimal",
            },
            body: JSON.stringify({ token }),
          },
        );
        if (!eventResponse.ok) {
          console.error("Could not persist tracking event", eventResponse.status);
        }
      }
    } catch (error) {
      console.error(
        "Tracking request failed",
        error instanceof Error ? error.name : "unknown",
      );
    }
  }

  return new Response(transparentPixel, {
    headers: {
      "Content-Type": "image/gif",
      "Cache-Control": "private, no-store, max-age=0",
      "X-Content-Type-Options": "nosniff",
    },
  });
});
