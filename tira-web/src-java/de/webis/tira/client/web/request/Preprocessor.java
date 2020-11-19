package de.webis.tira.client.web.request;

import javax.servlet.http.HttpServletRequest;

public class Preprocessor {
	
	private static final String TIRA = "/tira";
	
	public static final String getContextPath(HttpServletRequest req) {
		return getContextPath(req.getContextPath());
	}
	
	public static final String getContextPath(String contextPath) {
		return TIRA.equals(contextPath) ? "" : contextPath;
	}
}
