package de.webis.tira.client.web;

import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.response.Renderer;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import java.io.IOException;


@WebServlet(ConnectServlet.ROUTE)
@SuppressWarnings("serial")
public class ConnectServlet extends HttpServlet {

    public static final String ROUTE = "/connect/*";
    public static final String ROUTE_TUNNEL = "/tunnel/",
            ROUTE_CFG = "/cfg/";

    private static final String TEMPLATE_TASK_USER_RDP = "templates/tira-task-user-rdp-body.mustache",
            TEMPLATE_TASK_USER_RDP_FULL = "templates/tira-task-user-rdp-body-full.mustache",
            TEMPLATE_ERROR = "templates/tira-error.mustache",
            TEMPLATE_REMOTE_SETTINGS = "templates/tira-remote-config.mustache";

    @Override
    protected void
    doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        String path = req.getPathInfo();
        if (path.matches(ROUTE_TUNNEL))
            getRoute1(req, resp);
        else if (path.matches(ROUTE_CFG))
            getRouteCFG(req, resp);
        else
            getRouteError(req, resp);
    }

    protected void
    getRouteError(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {


        Renderer.render(getServletContext(), req, resp, TEMPLATE_ERROR);

    }

    protected void
    getRouteCFG(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {

        //check for authentication, respond with error if not
        if (Authenticator.signedInUser(req) == null)
            Renderer.render(getServletContext(), req, resp, TEMPLATE_ERROR);
        else {
            Renderer.render(getServletContext(), req, resp, TEMPLATE_REMOTE_SETTINGS);
        }
    }

    protected void
    getRoute1(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {

        //check for authentification, respond with error if not
        if (Authenticator.signedInUser(req) == null)
            Renderer.render(getServletContext(), req, resp, TEMPLATE_ERROR);
        else
            Renderer.render(getServletContext(), req, resp, TEMPLATE_TASK_USER_RDP);
        //Renderer.render(getServletContext(), req, resp, TEMPLATE_REMOTE_SETTINGS);

    }

    protected void
    doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {

        //check for authentification, respond with error if not logged in
        if (Authenticator.signedInUser(req) == null)
            Renderer.render(getServletContext(), req, resp, TEMPLATE_ERROR);
        else {
            //save post parameters in session


            req.getSession().setAttribute("protocol", req.getParameter("protocol"));
            req.getSession().setAttribute("resolution", req.getParameter("resolution"));
            req.getSession().setAttribute("depth", req.getParameter("depth"));
            req.getSession().setAttribute("layout", req.getParameter("layout"));
            req.getSession().setAttribute("fullscreen", req.getParameter("fullscreen"));

            if (req.getParameter("fullscreen").equals("true"))
                Renderer.render(getServletContext(), req, resp, TEMPLATE_TASK_USER_RDP_FULL);
            else
                Renderer.render(getServletContext(), req, resp, TEMPLATE_TASK_USER_RDP);

        }
    }
}
