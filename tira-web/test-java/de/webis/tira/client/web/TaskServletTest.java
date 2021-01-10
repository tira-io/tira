package de.webis.tira.client.web;

import org.junit.Assert;
import org.junit.Test;

import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;

public class TaskServletTest {
	@Test
	public void bla() {
		TaskUser tu = TaskServlet.dummyUnpolyTestUser();
		
		Assert.assertNotNull(tu);
	}
}
