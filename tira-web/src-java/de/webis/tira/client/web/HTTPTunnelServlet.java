package de.webis.tira.client.web;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketAddress;
import java.net.SocketTimeoutException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Vector;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import org.glyptodon.guacamole.GuacamoleConnectionClosedException;
import org.glyptodon.guacamole.GuacamoleException;
import org.glyptodon.guacamole.GuacamoleResourceNotFoundException;
import org.glyptodon.guacamole.GuacamoleServerException;
import org.glyptodon.guacamole.GuacamoleUpstreamTimeoutException;
import org.glyptodon.guacamole.io.GuacamoleReader;
import org.glyptodon.guacamole.net.GuacamoleSocket;
import org.glyptodon.guacamole.net.GuacamoleTunnel;
import org.glyptodon.guacamole.net.InetGuacamoleSocket;
import org.glyptodon.guacamole.net.SimpleGuacamoleTunnel;
import org.glyptodon.guacamole.protocol.ConfiguredGuacamoleSocket;
import org.glyptodon.guacamole.protocol.GuacamoleConfiguration;
import org.glyptodon.guacamole.servlet.GuacamoleHTTPTunnelServlet;
import org.glyptodon.guacamole.servlet.GuacamoleSession;

import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages;


@WebServlet(HTTPTunnelServlet.ROUTE)
public class HTTPTunnelServlet
extends GuacamoleHTTPTunnelServlet {


    public static final String
        ROUTE = "/connect/cfg/tunnel";

    private static final String
    	TEMPLATE_TASK_USER_RDP = "templates/tira-task-user-rdp-body.mustache",
        TEMPLATE_ERROR = "templates/tira-error.mustache",
        TEMPLATE_RDP_ERROR = "templates/tira-error-rdp.mustache";

    private static final long serialVersionUID = 102831973239L;
    // create a hashmap with guacd server string as key and attached tunnels as vector of strings
    HashMap<String, Vector<String>> guacamole_connections = new HashMap<String, Vector<String>>();

    @Override
    protected void
    doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException {


        handleTunnelRequest(req, resp);
    }

    @Override
    protected void
    doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException /* IOException*/ {
      handleTunnelRequest(req, resp);
    }


    boolean verify_hosts(HttpServletRequest request, String host) throws IOException, GuacamoleUpstreamTimeoutException, GuacamoleServerException {
        // create a socket before adding the host to the list to validate

        try {
            int SOCKET_TIMEOUT = 15000;

            String host_adr[] = host.split(":");
            if (host_adr.length != 2)
                return false;

            int port = Integer.parseInt(host_adr[1]);
            SocketAddress address = new InetSocketAddress(
                    InetAddress.getByName(host_adr[0]),
                    port
            );

            // Connect with timeout
            Socket sock = new Socket();
            sock.connect(address, SOCKET_TIMEOUT);

            // Set read timeout
            sock.setSoTimeout(SOCKET_TIMEOUT);
            return true;
        }
        catch (SocketTimeoutException e) {

            throw new GuacamoleUpstreamTimeoutException("Connection timed out.", e);
        }
        catch (IOException e) {
            return false;
            //throw new GuacamoleServerException(e);
        }
    }
    void
    GetGuacamoleInstances(HttpServletRequest request)
            throws IOException, GuacamoleUpstreamTimeoutException, GuacamoleServerException {
        // check available guacamole daemons defined on the nfs host
        // creates a map with the connection count per guacd instance and saves it in the servlet context as "guac_hosts"
        ServletContext sc = request.getSession().getServletContext();

        // first start, read file and set 0
        if (sc.getAttribute("guac_hosts") == null) {
            String _guacamole_config_path = "/mnt/nfs/tira/model/guacamole-hosts/guacamole-hosts.txt";
            File GuacConfig = new File(_guacamole_config_path);
            if (GuacConfig.exists()) {

                InputStream stream = new FileInputStream(GuacConfig);
                BufferedReader br = new BufferedReader(new InputStreamReader(stream, "UTF-8"));
                Vector<String> hosts = new Vector();
                String line;
                // StringBuilder sb = new StringBuilder();
                while ((line = br.readLine()) != null) {
                    hosts.add(line);
                }
                HashMap<String, Integer> host_map = new HashMap();
                for (String host : hosts) {
                    if (verify_hosts(request, host))
                        host_map.put(host, 0);
                }
                sc.setAttribute("guac_hosts", host_map);
            }
            // TODO: implement error page-forwarding
        }

        //update actual instances
        else {
            HashMap<String, Integer> host_map = (HashMap<String, Integer>) sc.getAttribute("guac_hosts");

            if (guacamole_connections.size() > 0) {
                Iterator it = guacamole_connections.entrySet().iterator();
                while (it.hasNext()) {
                    Map.Entry<String, Vector<String>> entry = (Map.Entry) it.next();
                    int count = entry.getValue().size();
                    if (count != host_map.get(entry.getKey())) {
                        host_map.put(entry.getKey(), count);
                    }
                }
                sc.setAttribute("guac_host", host_map);

            }
            //update from file
            String _guacamole_config_path = "/mnt/nfs/tira/model/guacamole-hosts/guacamole-hosts.txt";
            File GuacConfig = new File(_guacamole_config_path);
            if (GuacConfig.exists()) {

                InputStream stream = new FileInputStream(GuacConfig);
                BufferedReader br = new BufferedReader(new InputStreamReader(stream, "UTF-8"));
                Vector<String> hosts = new Vector();
                String line;

                while ((line = br.readLine()) != null) {
                    hosts.add(line);
                }

                Vector<String> to_delete_hosts = new Vector<>();
                for (String host : hosts) {
                    if (verify_hosts(request, host) && !host_map.containsKey(host)) {
                        host_map.put(host, 0);
                    }
                }

                // clear internal map of hosts if file entry was deleted
                Iterator it = host_map.entrySet().iterator();
                while (it.hasNext()) {
                    Map.Entry<String, Integer> entry = (Map.Entry) it.next();
                    if (!hosts.contains(entry.getKey())) {
                        to_delete_hosts.add(entry.getKey());
                    }
                }

                for (String s : to_delete_hosts){
                    host_map.remove(s);
                    guacamole_connections.remove(s);
                }

                sc.setAttribute("guac_hosts", host_map);
            }
        }
    }
    void handledisconnect(String tunnelUUID){
        // delete tunnel id from list to keep track of active connections
        Iterator it = guacamole_connections.entrySet().iterator();
        while (it.hasNext()){
            Map.Entry<String, Vector<String>> entry = (Map.Entry)it.next();
            if (entry.getValue().contains(tunnelUUID)){
                entry.getValue().remove(tunnelUUID);
            }
        }

    }

    // copied guacamole function with added tunnel detach callback
    @Override
    protected void doRead(HttpServletRequest request, HttpServletResponse response, String tunnelUUID) throws GuacamoleException {

        HttpSession httpSession = request.getSession(false);
        GuacamoleSession session = new GuacamoleSession(httpSession);

        // Get tunnel, ensure tunnel exists
        GuacamoleTunnel tunnel = session.getTunnel(tunnelUUID);
        if (tunnel == null)
            throw new GuacamoleResourceNotFoundException("No such tunnel.");

        // Ensure tunnel is open
        if (!tunnel.isOpen())
            throw new GuacamoleResourceNotFoundException("Tunnel is closed.");

        // Obtain exclusive read access
        GuacamoleReader reader = tunnel.acquireReader();

        try {

            // Note that although we are sending text, Webkit browsers will
            // buffer 1024 bytes before starting a normal stream if we use
            // anything but application/octet-stream.
            response.setContentType("application/octet-stream");
            response.setHeader("Cache-Control", "no-cache");

            // Get writer for response
            Writer out = new BufferedWriter(new OutputStreamWriter(
                    response.getOutputStream(), "UTF-8"));

            // Stream data to response, ensuring output stream is closed
            try {

                // Detach tunnel and throw error if EOF (and we haven't sent any
                // data yet.
                char[] message = reader.read();
                if (message == null)
                    throw new GuacamoleConnectionClosedException("Tunnel reached end of stream.");

                // For all messages, until another stream is ready (we send at least one message)
                do {

                    // Get message output bytes
                    out.write(message, 0, message.length);

                    // Flush if we expect to wait
                    if (!reader.available()) {
                        out.flush();
                        response.flushBuffer();
                    }

                    // No more messages another stream can take over
                    if (tunnel.hasQueuedReaderThreads())
                        break;

                } while (tunnel.isOpen() && (message = reader.read()) != null);

                // Close tunnel immediately upon EOF
                if (message == null) {
                    session.detachTunnel(tunnel);
                    tunnel.close();
                    handledisconnect(tunnelUUID);
                }

                // End-of-instructions marker
                out.write("0.;");
                out.flush();
                response.flushBuffer();
            }

            // Send end-of-stream marker and close tunnel if connection is closed
            catch (GuacamoleConnectionClosedException e) {

                // Detach and close
                session.detachTunnel(tunnel);
                tunnel.close();
                handledisconnect(tunnelUUID);

                // End-of-instructions marker
                out.write("0.;");
                out.flush();
                response.flushBuffer();
            }

            catch (GuacamoleException e) {

                // Detach and close
                session.detachTunnel(tunnel);
                tunnel.close();
                handledisconnect(tunnelUUID);

                throw e;
            }
            // Always close output stream
            finally {
                out.close();
            }
        }
        catch (IOException e) {
            // Log typically frequent I/O error if desired
            //logger.debug("Error writing to servlet output stream", e);

            // Detach and close
            session.detachTunnel(tunnel);
            tunnel.close();
            handledisconnect(tunnelUUID);
        }
        finally {
            tunnel.releaseReader();
        }
    }

    @Override
    protected GuacamoleTunnel doConnect(HttpServletRequest request)
            throws GuacamoleException {

        try {
           GetGuacamoleInstances(request);
        } catch (IOException e) {
            e.printStackTrace();
        }

        TiraClientWebMessages.User u;
		try {
			u = Authenticator.signedInUser(request);
		} catch (ServletException e) {
			throw new RuntimeException(e);
		}
        ServletContext sc = request.getSession().getServletContext();

        // get deamon with lowest usage
        HashMap<String, Integer> host_map = (HashMap)sc.getAttribute("guac_hosts");
        Map.Entry<String, Integer> lowest = null;

        if (host_map != null) {
            for (Map.Entry<String, Integer> deamon : host_map.entrySet()) {
                if (lowest == null || lowest.getValue() > deamon.getValue())
                    lowest = deamon;
            }
            //increment counter
            int count = host_map.get(lowest.getKey());
            count++;
            host_map.put(lowest.getKey(), count);
            sc.setAttribute("guac_hosts", host_map);
            request.getSession().setAttribute("current_guac_connection", lowest.getKey());

        }else
            System.out.println("DEBUG: No valid guacamole hosts available");


        String host[] = lowest.getKey().split(":");

        // check session vars
        String resolution = (String) request.getSession().getAttribute("resolution");
        String depth = (String) request.getSession().getAttribute("depth");
        String layout = (String) request.getSession().getAttribute("layout");
        String protocol = (String) request.getSession().getAttribute("protocol");

        String user_host = u.getHost();
        String user_port = u.getPortRdp();
        String user_name = u.getUserName();
        String user_pass = u.getUserPw();

        // Create our configuration
        GuacamoleConfiguration config = new GuacamoleConfiguration();

        // rdp config
        if (protocol.equals("rdp")) {
            String res[] = resolution.split("x");
            if (res.length == 2) {
                config.setParameter("width", res[0]);
                config.setParameter("height", res[1]);
            }
            config.setParameter("color-depth", depth);
            config.setParameter("server-layout", layout);
            config.setProtocol("rdp");
            config.setParameter("hostname", user_host);
            config.setParameter("port", user_port);
            config.setParameter("username", user_name);
            config.setParameter("password", user_pass);
        } else if (protocol.equals("ssh")){
            config.setProtocol("ssh");
            config.setParameter("hostname", u.getHost());
            config.setParameter("port", u.getPortSsh());
            config.setParameter("username", user_name);
            config.setParameter("password", user_pass);
        }

        InetGuacamoleSocket gSock = new InetGuacamoleSocket(host[0], Integer.parseInt(host[1]));


        //InetGuacamoleSocket gSock = new InetGuacamoleSocket("webis58.medien.uni-weimar.de", 4822);
        GuacamoleSocket socket = new ConfiguredGuacamoleSocket(gSock, config);

        // Establish the tunnel using the connected socket
        GuacamoleTunnel tunnel = new SimpleGuacamoleTunnel(socket);

        // save host and tunnel id
        String current_id = tunnel.getUUID().toString();


        if (guacamole_connections.get(lowest.getKey()) == null){
            Vector<String> tunnel_list = new Vector<String>();
            tunnel_list.add(current_id);
            guacamole_connections.put(lowest.getKey(), tunnel_list);
        } else{
            Vector<String> tunnel_list = guacamole_connections.get(lowest.getKey());
            tunnel_list.add(current_id);
            guacamole_connections.put(lowest.getKey(), tunnel_list);
        }

        // Attach tunnel to session
        HttpSession httpSession = request.getSession(true);
        GuacamoleSession session = new GuacamoleSession(httpSession);

        session.attachTunnel(tunnel);

        // Return pre-attached tunnel
        return tunnel;

    }

}
