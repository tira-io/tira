package de.webis.tira.client.web;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import de.webis.tira.client.web.request.Checker;
import de.webis.tira.client.web.response.Renderer;

@WebServlet(IndexServlet.ROUTE)
@SuppressWarnings("serial")
public class IndexServlet extends HttpServlet {
	
	public static final String ROUTE = "/";
	
	private static final String 
		TEMPLATE_INDEX = "/templates/tira-index.mustache";

	@Override
	protected void 
	doGet(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		if (!checkRequest1(req, resp)) return;
		Renderer.render(getServletContext(), req, resp, TEMPLATE_INDEX);

	}
	
	private boolean
	checkRequest1(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Checker c = Checker.getInstance();
		if (!c.checkPathIsEmpty(req, resp)) return false;
		return true;
	}
}
